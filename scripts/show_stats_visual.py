#!/usr/bin/env python3
"""
Visual demonstration of how the enhanced statistics appear in-game.
Shows formatted output for main menu, victory, and death screens.
"""


def show_visual_examples():
    """Display formatted examples of stat displays."""
    
    print("\n" + "="*80)
    print(" "*20 + "ENHANCED STATISTICS VISUAL EXAMPLES")
    print("="*80)
    
    # Example 1: First-time player (no stats yet)
    print("\n" + "─"*80)
    print("EXAMPLE 1: First-Time Player")
    print("─"*80)
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                    JEDI FUGITIVE                             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    💫 Force Echo #1
    
    [N] New Game
    [Q] Quit
    """)
    
    # Example 2: Returning player with good stats
    print("\n" + "─"*80)
    print("EXAMPLE 2: Returning Player (Good Performance)")
    print("─"*80)
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                    JEDI FUGITIVE                             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    💫 Force Echo #47
       ⭐ Souls Redeemed: 32
       💀 Fallen to Darkness: 15
       ⚖️ Balance Ratio: 68.1%
       ⚔️ Total Kills: 1,245
       📊 K/D Ratio: 83.00
       🔥 Best Streak: 9
    
    [N] New Game
    [L] Load Save
    [Q] Quit
    """)
    
    # Example 3: Returning player on hot streak
    print("\n" + "─"*80)
    print("EXAMPLE 3: Player on Hot Streak")
    print("─"*80)
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║                    JEDI FUGITIVE                             ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    
    💫 Force Echo #25
       ⭐ Souls Redeemed: 18
       💀 Fallen to Darkness: 7
       ⚖️ Balance Ratio: 72.0%
       ⚔️ Total Kills: 891
       📊 K/D Ratio: 127.29
       🔥 Best Streak: 12
    
    [N] New Game
    [Q] Quit
    """)
    
    # Example 4: Victory Screen
    print("\n" + "─"*80)
    print("EXAMPLE 4: Victory Screen")
    print("─"*80)
    print("""
    ════════════════════════════════════════════════════════════════
                        🌟 VICTORY! 🌟
    ════════════════════════════════════════════════════════════════
    
                    You have escaped the planet!
                The Force was with you on this journey.
    
                      YOUR FINAL STATISTICS:
    
                      Level: 12
                      Enemies Defeated: 67
                      Turns Survived: 342
                      Light Level: 8 | Dark Level: 4
                      Corruption: 23%
    
    ═══ LIFETIME STATISTICS ═══
    Total Runs: 48
    Victories: 33
    Deaths: 15
    Win Rate: 68.8%
    Total Kills: 1,312
    K/D Ratio: 87.47
    Win Streak: 4
    
                May the Force be with you, always.
    
    ════════════════════════════════════════════════════════════════
    [P] Play Again
    [Q] Quit
    ════════════════════════════════════════════════════════════════
    """)
    
    # Example 5: Death Screen
    print("\n" + "─"*80)
    print("EXAMPLE 5: Death Screen")
    print("─"*80)
    print("""
    ════════════════════════════════════════════════════════════════
                        💀 DEFEAT 💀
    ════════════════════════════════════════════════════════════════
    
                      You have fallen in battle.
    
                      YOUR FINAL STATISTICS:
    
                      Level: 5
                      Enemies Defeated: 23
                      Turns Survived: 156
                      Cause of Death: Sith Warrior
                      Location: Tomb Level 2
    
        Sith Lord: "Your journey ends here, Jedi. The Dark Side
                    claims another victim..."
    
                  The Dark Side has claimed another victim...
    
    === LIFETIME STATISTICS ===
    Total Runs: 49
    Victories: 33
    Deaths: 16
    Win Rate: 67.3%
    Total Kills: 1,335
    K/D Ratio: 83.44
    
    ════════════════════════════════════════════════════════════════
    [P] Play Again
    [Q] Quit
    ════════════════════════════════════════════════════════════════
    """)
    
    # Example 6: Perfect Record
    print("\n" + "─"*80)
    print("EXAMPLE 6: Perfect Record (No Deaths)")
    print("─"*80)
    print("""
    💫 Force Echo #8
       ⭐ Souls Redeemed: 8
       💀 Fallen to Darkness: 0
       ⚖️ Balance Ratio: 100.0%
       ⚔️ Total Kills: 387
       📊 K/D Ratio: 387.00
       🔥 Best Streak: 8
    
    [N] New Game
    [Q] Quit
    """)
    
    # Example 7: Speedrun Record
    print("\n" + "─"*80)
    print("EXAMPLE 7: After Setting Speed Record")
    print("─"*80)
    print("""
    ═══ LIFETIME STATISTICS ═══
    Total Runs: 35
    Victories: 24
    Deaths: 11
    Win Rate: 68.6%
    Total Kills: 892
    K/D Ratio: 81.09
    Win Streak: 1
    Highest Level: 14
    Most Enemies Killed (Single Run): 89
    Fastest Victory: 127 turns  ⚡ NEW RECORD!
    """)
    
    # Example 8: Stat Evolution
    print("\n" + "─"*80)
    print("EXAMPLE 8: Stat Progression Over Time")
    print("─"*80)
    print("""
    Run #1:  Win Rate: 0.0%   | K/D: 0.00   | Kills: 0
    Run #5:  Win Rate: 40.0%  | K/D: 18.00  | Kills: 72
    Run #10: Win Rate: 60.0%  | K/D: 45.50  | Kills: 273
    Run #25: Win Rate: 64.0%  | K/D: 67.22  | Kills: 605
    Run #50: Win Rate: 66.0%  | K/D: 78.43  | Kills: 1,412
    Run #100: Win Rate: 68.0% | K/D: 89.75  | Kills: 2,872
    
    Showing clear skill progression! 📈
    """)
    
    print("\n" + "="*80)
    print("End of Visual Examples")
    print("="*80)
    print("""
Key Visual Elements:
    ⭐ = Victories (Souls Redeemed)
    💀 = Deaths (Fallen to Darkness)
    ⚖️ = Win Rate (Balance Ratio)
    ⚔️ = Total Kills
    📊 = K/D Ratio
    🔥 = Win Streak
    ⚡ = New Record
    
All stats persist across sessions and are stored in:
    ~/.jedi_fugitive/game_stats.json
    """)


if __name__ == "__main__":
    show_visual_examples()
