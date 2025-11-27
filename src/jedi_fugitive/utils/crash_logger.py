"""
Comprehensive crash and error logging system for Dark Meridian.
Logs all errors, warnings, and game state to help debug issues.
"""
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


class CrashLogger:
    """Singleton logger that writes detailed crash reports to file."""
    
    _instance = None
    _log_file = None
    _session_start = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CrashLogger, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the logger and create log file."""
        try:
            # Create logs directory if it doesn't exist
            log_dir = Path(__file__).parent.parent.parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            
            # Create log file with timestamp
            self._session_start = datetime.now()
            timestamp = self._session_start.strftime("%Y%m%d_%H%M%S")
            self._log_file = log_dir / f"game_crash_log_{timestamp}.txt"
            
            # Write header
            with open(self._log_file, 'w') as f:
                f.write("="*80 + "\n")
                f.write("DARK MERIDIAN - CRASH & ERROR LOG\n")
                f.write("="*80 + "\n")
                f.write(f"Session started: {self._session_start.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Python version: {sys.version}\n")
                f.write(f"Platform: {sys.platform}\n")
                f.write("="*80 + "\n\n")
            
            print(f"[LOGGER] Crash logging enabled: {self._log_file}")
            
        except Exception as e:
            print(f"[LOGGER] Warning: Could not initialize crash logger: {e}")
            self._log_file = None
    
    def log_error(self, error_type, message, exception=None, game_state=None):
        """
        Log an error with full details.
        
        Args:
            error_type: Type of error (e.g., "CRASH", "ERROR", "WARNING")
            message: Description of what happened
            exception: The exception object (if any)
            game_state: Dict with relevant game state info
        """
        if not self._log_file:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self._log_file, 'a') as f:
                f.write("\n" + "="*80 + "\n")
                f.write(f"[{timestamp}] {error_type}: {message}\n")
                f.write("="*80 + "\n")
                
                # Write exception details
                if exception:
                    f.write(f"\nException Type: {type(exception).__name__}\n")
                    f.write(f"Exception Message: {str(exception)}\n")
                    f.write("\nStack Trace:\n")
                    f.write(traceback.format_exc())
                    f.write("\n")
                
                # Write game state
                if game_state:
                    f.write("\nGame State at Time of Error:\n")
                    f.write("-"*40 + "\n")
                    for key, value in game_state.items():
                        f.write(f"  {key}: {value}\n")
                    f.write("\n")
                
                f.write("="*80 + "\n")
                f.flush()
            
            print(f"[LOGGER] Error logged: {error_type} - {message}")
            
        except Exception as e:
            print(f"[LOGGER] Failed to write log: {e}")
    
    def log_info(self, message):
        """Log an informational message."""
        if not self._log_file:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self._log_file, 'a') as f:
                f.write(f"[{timestamp}] INFO: {message}\n")
                f.flush()
        except Exception:
            pass
    
    def log_game_event(self, event_type, details):
        """Log significant game events for debugging."""
        if not self._log_file:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self._log_file, 'a') as f:
                f.write(f"[{timestamp}] EVENT [{event_type}]: {details}\n")
                f.flush()
        except Exception:
            pass
    
    def get_game_state_snapshot(self, game_manager):
        """
        Extract relevant game state for error reporting.
        
        Args:
            game_manager: The GameManager instance
            
        Returns:
            Dict with game state information
        """
        try:
            state = {}
            
            if hasattr(game_manager, 'player'):
                p = game_manager.player
                state['player_x'] = getattr(p, 'x', None)
                state['player_y'] = getattr(p, 'y', None)
                state['player_hp'] = getattr(p, 'hp', None)
                state['player_max_hp'] = getattr(p, 'max_hp', None)
                state['player_level'] = getattr(p, 'level', None)
                state['player_stress'] = getattr(p, 'stress', None)
                state['player_corruption'] = getattr(p, 'dark_corruption', None)
                state['player_force_points'] = getattr(p, 'force_points', None)
                state['in_tomb'] = getattr(p, 'tomb_floor', None) is not None
                state['tomb_floor'] = getattr(p, 'tomb_floor', None)
            
            state['turn_count'] = getattr(game_manager, 'turn_count', None)
            state['running'] = getattr(game_manager, 'running', None)
            state['death'] = getattr(game_manager, 'death', None)
            state['victory'] = getattr(game_manager, 'victory', None)
            
            if hasattr(game_manager, 'enemies'):
                state['enemy_count'] = len(game_manager.enemies) if game_manager.enemies else 0
            
            if hasattr(game_manager, 'game_map'):
                state['map_height'] = len(game_manager.game_map) if game_manager.game_map else 0
                state['map_width'] = len(game_manager.game_map[0]) if game_manager.game_map and game_manager.game_map else 0
            
            return state
            
        except Exception as e:
            return {'error_getting_state': str(e)}
    
    def close(self):
        """Close the log file and write session summary."""
        if not self._log_file:
            return
        
        try:
            session_end = datetime.now()
            duration = session_end - self._session_start
            
            with open(self._log_file, 'a') as f:
                f.write("\n" + "="*80 + "\n")
                f.write("SESSION ENDED\n")
                f.write("="*80 + "\n")
                f.write(f"End time: {session_end.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Session duration: {duration}\n")
                f.write("="*80 + "\n")
            
            print(f"[LOGGER] Session log closed: {self._log_file}")
            
        except Exception:
            pass


# Global logger instance
_logger = None


def get_logger():
    """Get the global logger instance."""
    global _logger
    if _logger is None:
        _logger = CrashLogger()
    return _logger


def log_error(error_type, message, exception=None, game_state=None):
    """Convenience function to log an error."""
    get_logger().log_error(error_type, message, exception, game_state)


def log_info(message):
    """Convenience function to log info."""
    get_logger().log_info(message)


def log_game_event(event_type, details):
    """Convenience function to log game events."""
    get_logger().log_game_event(event_type, details)


def safe_execute(func, error_msg="Operation failed", game_manager=None):
    """
    Execute a function and log any errors that occur.
    
    Args:
        func: Function to execute
        error_msg: Description of what failed
        game_manager: GameManager instance for state snapshot
        
    Returns:
        Result of func() or None if error occurred
    """
    try:
        return func()
    except Exception as e:
        logger = get_logger()
        game_state = None
        if game_manager:
            game_state = logger.get_game_state_snapshot(game_manager)
        logger.log_error("ERROR", error_msg, e, game_state)
        return None
