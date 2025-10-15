# Auto Key Holder (Pattern)

A powerful PyQt6-based automation tool for keyboard input with customizable patterns and constant key holding capabilities. This tool allows you to automate keyboard inputs with precise timing control, supporting both continuous key holding and complex key press patterns.

## **Illustration**
<img width="601" height="853" alt="image" src="https://github.com/user-attachments/assets/b4475189-b226-42e1-aaec-c50491d9d929" />

## What Can It Do?

- Hold down any key continuously with a single hotkey
- Create complex key press patterns with custom timing
- Mix fixed and random timing for unpredictable patterns
- Control everything with global hotkeys from any application
- Save and load different configurations for various uses

## Features

- **Constant Key Mode**: Hold down a single key continuously
- **Pattern Mode**: Execute complex key patterns with customizable timing
- **Two Timing Modes**: Custom (fixed) and Random (ranged) durations
- **Global Hotkeys**: Control the application from any window
- **Save/Load System**: Store and recall your configurations
- **User-Friendly GUI**: Easy-to-use interface for pattern management

## Setup

1. Install Python 3.8 or higher
2. Install required packages:
   ```bash
   pip install PyQt6
   pip install keyboard
   ```
   or 
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python auto_key_holder.py
   ```

## Quick Start Guide

### Constant Key Mode
1. Click "Listen" to capture key
2. Set global hotkey
3. Start/Stop with button or hotkey

### Pattern Mode
1. Add patterns with custom/random timing
2. Set global pattern hotkey
3. Configure repetitions (-1 = infinite)
4. Start/Stop with button or hotkey

### Save/Load
- Save configs to reuse later
- Load saved configs anytime
- Independent saves for constant/pattern modes

## Advanced Usage

### Pattern Timing Control
- **Custom Mode**: Set exact hold and wait times
- **Random Mode**: Define time ranges for unpredictable patterns
- **Mixed Mode**: Some patterns fixed, others random
- **Zero Wait Time**: For rapid key presses
- **Long Hold Times**: For sustained key presses

### Pattern Examples
1. **Basic Macro**: Single key, fixed timing
   - Hold: 0.1s, Wait: 0.1s
   - Good for regular clicking

2. **Variable Clicking**: Random timing
   - Hold: 0.1s-0.2s
   - Wait: 0.1s-0.3s
   - Creates natural-looking input patterns

3. **Complex Sequence**: Multiple keys
   - Different timing for each key
   - Mix of random and fixed timings
   - Create sophisticated automation patterns

### Pro Tips
- Use shorter hold times for tap-like actions
- Longer hold times for sustained actions
- Start with longer timings and adjust down
- Test patterns with safe keys first
- Save different configs for different applications

## Troubleshooting

### Common Issues
1. **Hotkeys Not Working**
   - Run as administrator
   - Check for conflicts
   - Restart application

2. **Patterns Stop**
   - Verify timing values
   - Check for system interruptions
   - Ensure no conflicting applications

3. **Performance Issues**
   - Reduce number of active patterns
   - Increase timing intervals
   - Close unnecessary applications

### Safety Notes
- Always have a way to stop patterns
- Test in safe environments first
- Backup configurations regularly
- Monitor system performance

### Note: This application requires administrative privileges to use global hotkeys and keyboard control functions.

