import base64
import json
import socket
import threading
import time
import socks
import websocket
from .config import Config
from .function_handlers import FunctionHandler

# Proxy setup is now handled per-connection, not globally.
class WebSocketClient:
    def __init__(self, audio_manager):
        self.config = Config()
        self.audio_manager = audio_manager
        self.ws = None
        self.function_handler = FunctionHandler()
        
    def create_connection_with_ipv4(self, *args, **kwargs):
        """Create a WebSocket connection using IPv4"""
        original_getaddrinfo = socket.getaddrinfo

        def getaddrinfo_ipv4(host, port, family=socket.AF_INET, *args):
            return original_getaddrinfo(host, port, socket.AF_INET, *args)

        socket.getaddrinfo = getaddrinfo_ipv4
        try:
            return websocket.create_connection(*args, **kwargs)
        finally:
            socket.getaddrinfo = original_getaddrinfo
    
    def send_mic_audio_to_websocket(self):
        """Send microphone audio data to the WebSocket"""
        try:
            while not self.audio_manager.stop_event.is_set():
                try:
                    # Use timeout to prevent blocking indefinitely
                    mic_chunk = self.audio_manager.mic_queue.get(timeout=0.1)
                    # print(f'🎤 Sending {len(mic_chunk)} bytes of audio data.')
                    encoded_chunk = base64.b64encode(mic_chunk).decode('utf-8')
                    message = json.dumps({
                        'type': 'input_audio_buffer.append', 
                        'audio': encoded_chunk
                    })
                    try:
                        if self.ws and self.ws.sock:
                            self.ws.send(message)
                    except Exception as e:
                        print(f'Error sending mic audio: {e}')
                        break
                except:
                    # Queue is empty or timeout, continue
                    continue
        except Exception as e:
            print(f'Exception in send_mic_audio_to_websocket thread: {e}')
        finally:
            print('Exiting send_mic_audio_to_websocket thread.')
    
    def receive_audio_from_websocket(self):
        """Receive audio data from the WebSocket and process events"""
        try:
            while not self.audio_manager.stop_event.is_set():
                try:
                    # Set a timeout to prevent blocking
                    self.ws.settimeout(1.0)
                    message = self.ws.recv()
                    
                    if not message:
                        print('🔵 Received empty message (possibly EOF or WebSocket closing).')
                        break

                    message = json.loads(message)
                    event_type = message['type']
                    print(f'⚡️ Received WebSocket event: {event_type}')

                    self._handle_websocket_event(event_type, message)

                except websocket.WebSocketTimeoutException:
                    # Timeout is expected, continue
                    continue
                except Exception as e:
                    print(f'Error receiving audio: {e}')
                    break
        except Exception as e:
            print(f'Exception in receive_audio_from_websocket thread: {e}')
        finally:
            print('Exiting receive_audio_from_websocket thread.')
    
    def _handle_websocket_event(self, event_type, message):
        """Handle different WebSocket event types"""
        if event_type == 'session.created':
            self._send_session_update()
            
        elif event_type == 'response.audio.delta':
            audio_content = base64.b64decode(message['delta'])
            self.audio_manager.add_audio_data(audio_content)
            
        elif event_type == 'input_audio_buffer.speech_started':
            print('🔵 Speech started, clearing buffer and stopping playback.')
            self.audio_manager.clear_audio_buffer()
            self.audio_manager.stop_audio_playback()
            
        elif event_type == 'response.audio.done':
            print('🔵 AI finished speaking.')
            
        elif event_type == 'response.function_call_arguments.done':
            self.function_handler.handle_function_call(message, self.ws)
            
        elif event_type == 'conversation.item.input_audio_transcription.completed':
            transcript = message.get('transcript', 'No transcript available')
            print(f'🎯 Transcription completed: "{transcript}"')
            
        elif event_type == 'response.created':
            print('🎤 AI is preparing response...')
            
        elif event_type == 'response.done':
            status = message.get('response', {}).get('status', 'unknown')
            print(f'✅ Response completed with status: {status}')
            
        elif event_type == 'conversation.item.created':
            item_type = message.get('item', {}).get('type', 'unknown')
            print(f'📝 Conversation item created: {item_type}')
            
        elif event_type == 'response.output_item.added':
            item_type = message.get('item', {}).get('type', 'unknown')
            print(f'➕ Output item added: {item_type}')
            
        elif event_type == 'response.content_part.added':
            part_type = message.get('part', {}).get('type', 'unknown')
            print(f'🔧 Content part added: {part_type}')
            
        elif event_type == 'response.audio_transcript.delta':
            transcript_delta = message.get('delta', '')
            print(f'🎙️ AI speaking: {transcript_delta}', end='', flush=True)
            
        elif event_type == 'response.audio_transcript.done':
            print('\n🔚 AI finished speaking transcript')
            
        else:
            # Log unknown events for debugging
            print(f'❓ Unknown event: {event_type}')
            if 'error' in message:
                print(f'❌ Error in message: {message["error"]}')
    
    def _send_session_update(self):
        """Send session configuration updates to the server"""
        session_config = self.function_handler.get_session_config()
        session_config_json = json.dumps(session_config)
        print(f"Send FC session update: {session_config_json}")

        try:
            self.ws.send(session_config_json)
        except Exception as e:
            print(f"Failed to send session update: {e}")
    
    def connect_to_openai(self):
        """Establish connection with OpenAI's WebSocket API"""
        try:
            self.ws = self.create_connection_with_ipv4(
                self.config.ws_url,
                header=[
                    f'Authorization: Bearer {self.config.api_key}',
                    'OpenAI-Beta: realtime=v1'
                ]
            )
            print('Connected to OpenAI WebSocket.')

            # Start the recv and send threads
            receive_thread = threading.Thread(target=self.receive_audio_from_websocket)
            receive_thread.start()

            mic_thread = threading.Thread(target=self.send_mic_audio_to_websocket)
            mic_thread.start()

            # Wait for stop_event to be set
            while not self.audio_manager.stop_event.is_set():
                time.sleep(0.1)

            # Send a close frame and close the WebSocket gracefully
            print('Sending WebSocket close frame.')
            self.ws.send_close()

            receive_thread.join()
            mic_thread.join()

            print('WebSocket closed and threads terminated.')
            
        except Exception as e:
            print(f'Failed to connect to OpenAI: {e}')
        finally:
            if self.ws is not None:
                try:
                    self.ws.close()
                    print('WebSocket connection closed.')
                except Exception as e:
                    print(f'Error closing WebSocket connection: {e}')