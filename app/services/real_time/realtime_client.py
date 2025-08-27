import time
from .audio_manager import AudioManager
from .websocket_client import WebSocketClient

class RealtimeClient:
    def __init__(self):
        self.audio_manager = AudioManager()
        self.ws_client = WebSocketClient(self.audio_manager)
        self.is_running = False
        
    def start(self):
        """Start the realtime client"""
        if self.is_running:
            print("Client is already running")
            return
            
        try:
            print("Starting realtime client...")
            self.is_running = True
            
            # Start audio streams
            self.audio_manager.start_streams()
            
            # Connect to OpenAI WebSocket
            self.ws_client.connect_to_openai()
            
            # Keep running while streams are active
            while self.audio_manager.is_streams_active() and self.is_running:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print('Gracefully shutting down...')
            self.stop()
        except Exception as e:
            print(f'Error in realtime client: {e}')
            self.stop()
    
    def stop(self):
        """Stop the realtime client"""
        if not self.is_running:
            return
            
        print("Stopping realtime client...")
        self.is_running = False
        
        # Stop audio manager
        self.audio_manager.stop_event.set()
        self.audio_manager.stop_streams()
        
        print('Realtime client stopped.')
    
    def is_active(self):
        """Check if the client is currently active"""
        return self.is_running and self.audio_manager.is_streams_active()

# Standalone execution
def main():
    client = RealtimeClient()
    try:
        client.start()
    finally:
        client.stop()

if __name__ == '__main__':
    main()