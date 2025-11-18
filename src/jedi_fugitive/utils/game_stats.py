"""
Persistent game statistics tracking.
Stores run counter and other stats across game sessions.
"""
import json
from pathlib import Path
from typing import Dict, Any


class GameStats:
    """Manages persistent game statistics."""
    
    def __init__(self, stats_file: str = None):
        """
        Initialize game stats tracker.
        
        Args:
            stats_file: Path to stats file. If None, uses default location.
        """
        if stats_file is None:
            # Store in user's home directory under .jedi_fugitive
            home = Path.home()
            stats_dir = home / ".jedi_fugitive"
            stats_dir.mkdir(exist_ok=True)
            self.stats_file = stats_dir / "game_stats.json"
        else:
            self.stats_file = Path(stats_file)
        
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict[str, Any]:
        """Load stats from file, or create default stats if file doesn't exist."""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                # If file is corrupted, start fresh
                return self._default_stats()
        else:
            return self._default_stats()
    
    def _default_stats(self) -> Dict[str, Any]:
        """Return default stats structure."""
        return {
            "total_runs": 0,
            "total_victories": 0,
            "total_deaths": 0,
            "highest_level": 0,
            "most_enemies_killed": 0,
        }
    
    def _save_stats(self):
        """Save stats to file."""
        try:
            # Ensure directory exists
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except IOError as e:
            # Fail silently - don't crash the game over stats
            print(f"Warning: Could not save game stats: {e}")
    
    def increment_runs(self) -> int:
        """
        Increment total run counter and save.
        
        Returns:
            The new total run count.
        """
        self.stats["total_runs"] = self.stats.get("total_runs", 0) + 1
        self._save_stats()
        return self.stats["total_runs"]
    
    def record_victory(self, player_level: int = 0, enemies_killed: int = 0):
        """
        Record a victory and update related stats.
        
        Args:
            player_level: Final player level
            enemies_killed: Total enemies killed this run
        """
        self.stats["total_victories"] = self.stats.get("total_victories", 0) + 1
        
        if player_level > self.stats.get("highest_level", 0):
            self.stats["highest_level"] = player_level
        
        if enemies_killed > self.stats.get("most_enemies_killed", 0):
            self.stats["most_enemies_killed"] = enemies_killed
        
        self._save_stats()
    
    def record_death(self, player_level: int = 0, enemies_killed: int = 0):
        """
        Record a death and update related stats.
        
        Args:
            player_level: Final player level
            enemies_killed: Total enemies killed this run
        """
        self.stats["total_deaths"] = self.stats.get("total_deaths", 0) + 1
        
        if player_level > self.stats.get("highest_level", 0):
            self.stats["highest_level"] = player_level
        
        if enemies_killed > self.stats.get("most_enemies_killed", 0):
            self.stats["most_enemies_killed"] = enemies_killed
        
        self._save_stats()
    
    def get_total_runs(self) -> int:
        """Get total number of game runs."""
        return self.stats.get("total_runs", 0)
    
    def get_total_victories(self) -> int:
        """Get total number of victories."""
        return self.stats.get("total_victories", 0)
    
    def get_total_deaths(self) -> int:
        """Get total number of deaths."""
        return self.stats.get("total_deaths", 0)
    
    def get_win_rate(self) -> float:
        """Get win rate as percentage."""
        total = self.get_total_runs()
        if total == 0:
            return 0.0
        return (self.get_total_victories() / total) * 100
    
    def get_stats_summary(self) -> str:
        """Get formatted stats summary."""
        runs = self.get_total_runs()
        victories = self.get_total_victories()
        deaths = self.get_total_deaths()
        win_rate = self.get_win_rate()
        
        lines = [
            f"Total Runs: {runs}",
            f"Victories: {victories}",
            f"Deaths: {deaths}",
            f"Win Rate: {win_rate:.1f}%",
        ]
        
        if self.stats.get("highest_level", 0) > 0:
            lines.append(f"Highest Level: {self.stats['highest_level']}")
        
        if self.stats.get("most_enemies_killed", 0) > 0:
            lines.append(f"Most Enemies Killed: {self.stats['most_enemies_killed']}")
        
        return "\n".join(lines)


# Global stats tracker instance
_game_stats = None


def get_game_stats() -> GameStats:
    """Get the global game stats instance."""
    global _game_stats
    if _game_stats is None:
        _game_stats = GameStats()
    return _game_stats
