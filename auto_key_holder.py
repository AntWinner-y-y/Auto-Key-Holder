import sys
import random
import time
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QRadioButton, QButtonGroup, QSpinBox, QListWidget,
                            QDoubleSpinBox, QGroupBox, QStackedWidget, QFrame,
                            QScrollArea, QWidgetItem, QComboBox, QMessageBox,
                            QInputDialog, QDialog, QListWidgetItem)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QColor
import keyboard

from threading import Event

class ConstantKeyThread(QThread):
    def __init__(self, key):
        super().__init__()
        self.key = key
        self.running = True
        self._stop_event = Event()

    def run(self):
        keyboard.press(self.key)
        self._stop_event.wait()  # More efficient than sleep loop
        keyboard.release(self.key)
        
    def stop(self):
        self.running = False
        self._stop_event.set()

class KeyHolderThread(QThread):
    pattern_complete = pyqtSignal()
    
    def __init__(self, patterns, use_random, repetitions, random_ranges=None):
        super().__init__()
        self.patterns = patterns
        self.use_random = use_random
        self.repetitions = repetitions
        self.random_ranges = random_ranges or {}
        self.running = True
        self._stop_event = Event()
        self._pattern_cache = []  # Cache for pattern timings
        self._prepare_pattern_cache()
        
    def _prepare_pattern_cache(self):
        """Pre-calculate pattern timings when not in random mode"""
        self._pattern_cache.clear()
        if not self.use_random:
            for pattern in self.patterns:
                try:
                    # Parse hold time
                    hold_str = str(pattern[1]).strip()
                    if '-' in hold_str:
                        hold_min, hold_max = map(float, hold_str.split('-'))
                        hold_value = hold_min if hold_min == hold_max else random.uniform(hold_min, hold_max)
                    else:
                        hold_value = float(hold_str)
                        
                    # Parse wait time
                    wait_str = str(pattern[2]).strip()
                    if '-' in wait_str:
                        wait_min, wait_max = map(float, wait_str.split('-'))
                        wait_value = wait_min if wait_min == wait_max else random.uniform(wait_min, wait_max)
                    else:
                        wait_value = float(wait_str)
                        
                    self._pattern_cache.append({
                        'key': pattern[0],
                        'hold': hold_value,
                        'wait': wait_value
                    })
                except (ValueError, IndexError, TypeError) as e:
                    print(f"Error processing pattern {pattern}: {e}")
                    continue
                
    def is_running(self):
        return self.isRunning() and self.running

    def run(self):
        completed_reps = 0
        last_key_pressed = None
        
        while self.running and (self.repetitions == -1 or completed_reps < self.repetitions):
            pattern_list = self._pattern_cache if not self.use_random else self.patterns
            if not pattern_list:
                print("No patterns to execute")
                break
                
            for pattern in pattern_list:
                if not self.running:
                    break
                    
                try:
                    # Safely release last key if it was pressed
                    if last_key_pressed is not None:
                        try:
                            keyboard.release(last_key_pressed)
                        except:
                            pass
                        last_key_pressed = None
                        
                    # Get the key and timing values
                    if isinstance(pattern, tuple):  # Random pattern format
                        key = pattern[0]
                        
                        # Parse hold time
                        if isinstance(pattern[1], str):
                            hold_str = pattern[1].strip()
                            if '-' in hold_str:
                                hold_min, hold_max = map(float, hold_str.split('-'))
                                actual_hold = hold_min if hold_min == hold_max else random.uniform(hold_min, hold_max)
                            else:
                                actual_hold = float(hold_str)
                        else:
                            actual_hold = float(pattern[1])
                        
                        # Parse wait time
                        if isinstance(pattern[2], str):
                            wait_str = pattern[2].strip()
                            if '-' in wait_str:
                                wait_min, wait_max = map(float, wait_str.split('-'))
                                actual_wait = wait_min if wait_min == wait_max else random.uniform(wait_min, wait_max)
                            else:
                                actual_wait = float(wait_str)
                        else:
                            actual_wait = float(pattern[2])
                    else:  # Custom pattern format
                        key = pattern['key']
                        actual_hold = float(pattern['hold'])
                        actual_wait = float(pattern['wait'])
                        
                    # Execute the key pattern
                    keyboard.press(key)
                    last_key_pressed = key
                    
                    # Hold the key for specified duration
                    hold_end = time.time() + actual_hold
                    while time.time() < hold_end:
                        if not self.running or self._stop_event.wait(timeout=0.01):
                            keyboard.release(key)
                            last_key_pressed = None
                            return
                            
                    # Release the key
                    keyboard.release(key)
                    last_key_pressed = None
                    
                    # Wait before next key
                    wait_end = time.time() + actual_wait
                    while time.time() < wait_end:
                        if not self.running or self._stop_event.wait(timeout=0.01):
                            return
                            
                except Exception as e:
                    print(f"Error executing pattern: {str(e)}")
                    if last_key_pressed is not None:
                        try:
                            keyboard.release(last_key_pressed)
                        except:
                            pass
                        last_key_pressed = None
                    continue
            
            # One repetition complete
            completed_reps += 1
            if self.repetitions != -1 and completed_reps >= self.repetitions:
                break
                
            # Small delay between repetitions to prevent high CPU usage
            if self.running:
                time.sleep(0.001)
        
        # Final cleanup
        if last_key_pressed is not None:
            try:
                keyboard.release(last_key_pressed)
            except:
                pass
        
        # Signal completion
        self.pattern_complete.emit()
        
    def stop(self):
        self.running = False
        self._stop_event.set()
        # Ensure all keys are released
        for pattern in self.patterns:
            try:
                key = pattern[0] if self.use_random else pattern['key']
                keyboard.release(key)
            except:
                pass
        
        self.pattern_complete.emit()

class TimeInputGroup(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        layout = QHBoxLayout(self)
        
        # Create spin boxes with better precision and range
        self.value_spin = QDoubleSpinBox()
        self.value_spin.setRange(0.0, 9999.0)  # Allow up to 9999 seconds
        self.value_spin.setSingleStep(0.1)
        self.value_spin.setDecimals(1)
        self.value_spin.setValue(1.0)
        
        layout.addWidget(self.value_spin)
        layout.addWidget(QLabel("seconds"))

class RandomRangeGroup(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        layout = QVBoxLayout(self)

        # Hold duration range
        hold_layout = QHBoxLayout()
        hold_layout.addWidget(QLabel("Hold Range:"))
        self.min_hold = QDoubleSpinBox()
        self.max_hold = QDoubleSpinBox()
        for spin in (self.min_hold, self.max_hold):
            spin.setRange(0.1, 9999.0)  # Hold time up to 9999 seconds
            spin.setSingleStep(0.1)
            spin.setDecimals(1)
        self.min_hold.setValue(0.5)
        self.max_hold.setValue(2.0)
        hold_layout.addWidget(self.min_hold)
        hold_layout.addWidget(QLabel("-"))
        hold_layout.addWidget(self.max_hold)
        hold_layout.addWidget(QLabel("seconds"))
        layout.addLayout(hold_layout)

        # Wait duration range
        wait_layout = QHBoxLayout()
        wait_layout.addWidget(QLabel("Wait Range:"))
        self.min_wait = QDoubleSpinBox()
        self.max_wait = QDoubleSpinBox()
        for spin in (self.min_wait, self.max_wait):
            spin.setRange(0.0, 9999.0)  # Allow up to 9999 seconds wait time
            spin.setSingleStep(0.1)
            spin.setDecimals(1)
        self.min_wait.setValue(0.0)  # Default to 0 for minimum wait
        self.max_wait.setValue(2.0)
        wait_layout.addWidget(self.min_wait)
        wait_layout.addWidget(QLabel("-"))
        wait_layout.addWidget(self.max_wait)
        wait_layout.addWidget(QLabel("seconds"))
        layout.addLayout(wait_layout)

class AutoKeyHolder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Key Holder")
        self.patterns = []
        self.random_ranges = {}
        self.pattern_widgets = []  # Store pattern widgets for easy access
        self.constant_key = None
        self.constant_key_thread = None
        self.is_constant_key_active = False
        self.is_listening = False
        self.current_input_target = None
        self.is_hotkey = False  # Flag to indicate if we're listening for a hotkey
        self.constant_hotkey = None  # Store constant key hotkey
        self.pattern_hotkey = None   # Store pattern hotkey
        self.pattern_thread = None   # Store the pattern thread
        self.is_pattern_active = False  # Flag for pattern state
        self.initUI()
        self.setup_global_hotkeys()
        
    def start_listening(self, input_widget, is_hotkey=False):
        if self.is_listening:
            return
            
        self.is_listening = True
        self.is_hotkey = is_hotkey
        self.current_input_target = input_widget
        input_widget.setText("Press key combination...")
        keyboard.on_press(self.on_key_press)
        
    def on_key_press(self, event):
        if self.is_listening and self.current_input_target:
            key_name = event.name
            # For hotkeys, we want to capture combinations
            if self.is_hotkey:
                # Get all currently pressed keys
                pressed_keys = keyboard.get_hotkey_name()
                if pressed_keys:
                    key_name = pressed_keys
                    
            # Set the text and ensure it's centered
            self.current_input_target.setText(key_name)
            
            # Update hotkeys if necessary
            if self.is_hotkey:
                # Check if the new hotkey is already in use
                is_duplicate = False
                if self.current_input_target == self.constant_hotkey_input:
                    if self.pattern_hotkey == key_name:
                        is_duplicate = True
                elif self.current_input_target == self.pattern_hotkey_input:
                    if self.constant_hotkey == key_name:
                        is_duplicate = True
                
                if is_duplicate:
                    QMessageBox.warning(self, "Warning", 
                                     "This hotkey is already in use. Please choose a different one.")
                    self.current_input_target.clear()
                else:
                    # Apply the new hotkey
                    if self.current_input_target == self.constant_hotkey_input:
                        self.update_constant_hotkey(key_name)
                    elif self.current_input_target == self.pattern_hotkey_input:
                        self.update_pattern_hotkey(key_name)
            else:
                # If it's not a hotkey, make sure the text is centered
                self.current_input_target.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Reset listening state
            keyboard.unhook_all()
            self.is_listening = False
            self.is_hotkey = False
            self.current_input_target = None
            # Only set up hotkeys that are active
            if self.constant_hotkey or self.pattern_hotkey:
                self.setup_global_hotkeys()  # Reconnect active hotkeys
            
    def setup_global_hotkeys(self):
        """Set up hotkeys with independent handlers for constant and pattern modes"""
        try:
            # Clear all existing hotkeys first
            keyboard.unhook_all()
            
            # Remove references to old handlers
            if hasattr(self, '_constant_hotkey_handler'):
                delattr(self, '_constant_hotkey_handler')
            if hasattr(self, '_pattern_hotkey_handler'):
                delattr(self, '_pattern_hotkey_handler')
            
            # Set up constant key hotkey
            if self.constant_hotkey:
                try:
                    self._constant_hotkey_handler = keyboard.add_hotkey(
                        self.constant_hotkey, 
                        self.toggle_constant_key, 
                        suppress=True,
                        trigger_on_release=False,  # Trigger immediately on press
                        timeout=0.1  # Reduce timeout for faster response
                    )
                    # Make sure the hotkey input shows the current hotkey
                    self.constant_hotkey_input.setText(self.constant_hotkey)
                except Exception as e:
                    print(f"Error setting up constant key hotkey: {e}")
                    self.constant_hotkey = None
                    self.constant_hotkey_input.clear()
            
            # Set up pattern hotkey
            if self.pattern_hotkey:
                try:
                    self._pattern_hotkey_handler = keyboard.add_hotkey(
                        self.pattern_hotkey, 
                        self.toggle_pattern, 
                        suppress=True,
                        trigger_on_release=False,  # Trigger immediately on press
                        timeout=0.1  # Reduce timeout for faster response
                    )
                    # Make sure the hotkey input shows the current hotkey
                    self.pattern_hotkey_input.setText(self.pattern_hotkey)
                except Exception as e:
                    print(f"Error setting up pattern hotkey: {e}")
                    self.pattern_hotkey = None
                    self.pattern_hotkey_input.clear()
                    
        except Exception as e:
            print(f"Error in setup_global_hotkeys: {e}")
            # In case of error, clear all hotkeys and reset state
            keyboard.unhook_all()
            self.constant_hotkey = None
            self.pattern_hotkey = None
            self.constant_hotkey_input.clear()
            self.pattern_hotkey_input.clear()
            
    def update_constant_hotkey(self, hotkey):
        """Update constant key hotkey without affecting pattern hotkey"""
        keyboard.unhook_all()  # Clear all hotkeys first
        
        self.constant_hotkey = hotkey
        if hotkey:
            try:
                self._constant_hotkey_handler = keyboard.add_hotkey(
                    hotkey, 
                    self.toggle_constant_key, 
                    suppress=True
                )
            except Exception as e:
                print(f"Error setting up constant key hotkey: {e}")
                self.constant_hotkey = None
                self.constant_hotkey_input.clear()
                
        # Re-add pattern hotkey if it exists
        if self.pattern_hotkey:
            try:
                self._pattern_hotkey_handler = keyboard.add_hotkey(
                    self.pattern_hotkey, 
                    self.toggle_pattern, 
                    suppress=True
                )
            except Exception:
                # If pattern hotkey fails, leave it for the next update
                pass
        
    def update_pattern_hotkey(self, hotkey):
        """Update pattern hotkey without affecting constant hotkey"""
        keyboard.unhook_all()  # Clear all hotkeys first
        
        self.pattern_hotkey = hotkey
        if hotkey:
            try:
                self._pattern_hotkey_handler = keyboard.add_hotkey(
                    hotkey, 
                    self.toggle_pattern, 
                    suppress=True
                )
            except Exception as e:
                print(f"Error setting up pattern hotkey: {e}")
                self.pattern_hotkey = None
                self.pattern_hotkey_input.clear()
                
        # Re-add constant hotkey if it exists
        if self.constant_hotkey:
            try:
                self._constant_hotkey_handler = keyboard.add_hotkey(
                    self.constant_hotkey, 
                    self.toggle_constant_key, 
                    suppress=True
                )
            except Exception:
                # If constant hotkey fails, leave it for the next update
                pass

    def save_constant_key(self):
        # Create saves directory if it doesn't exist
        if not os.path.exists("saves/constant"):
            os.makedirs("saves/constant")
            
        # Get list of existing saves
        save_files = [f for f in os.listdir("saves/constant") if f.endswith(".json")]
        save_names = [os.path.splitext(f)[0] for f in save_files]
        
        # Ask user for save name
        name, ok = QInputDialog.getText(self, "Save Constant Key", 
                                      "Enter a name for the constant key configuration:",
                                      QLineEdit.EchoMode.Normal)
        if ok and name:
            # Collect constant key settings
            constant_key_config = {
                "key": self.constant_key_input.text(),
                "hotkey": self.constant_hotkey
            }
            
            # Save to file
            filepath = os.path.join("saves/constant", f"{name}.json")
            if os.path.exists(filepath):
                reply = QMessageBox.question(self, "Confirm Overwrite",
                                          f"Constant key configuration '{name}' already exists. Overwrite?",
                                          QMessageBox.StandardButton.Yes | 
                                          QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return

            try:
                # Ensure the saves directory exists right before writing
                os.makedirs("saves/constant", exist_ok=True)
                with open(filepath, 'w') as f:
                    json.dump(constant_key_config, f, indent=4)
                QMessageBox.information(self, "Success", 
                                     f"Constant key configuration saved as '{name}'")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to save constant key configuration: {str(e)}")

    def save_pattern(self):
        # Create saves directory if it doesn't exist
        if not os.path.exists("saves/patterns"):
            os.makedirs("saves/patterns")
            
        # Get list of existing saves
        save_files = [f for f in os.listdir("saves/patterns") if f.endswith(".json")]
        save_names = [os.path.splitext(f)[0] for f in save_files]
        
        # Ask user for save name
        name, ok = QInputDialog.getText(self, "Save Pattern", 
                                      "Enter a name for the pattern configuration:",
                                      QLineEdit.EchoMode.Normal)
        if ok and name:
            # Collect all patterns
            patterns_config = []
            for i in range(len(self.patterns)):
                pattern = self.patterns[i]
                is_random = isinstance(pattern[1], str) and "-" in pattern[1]
                
                if is_random:
                    pattern_config = {
                        "key": pattern[0],
                        "mode": "Random",
                        "hold_range": pattern[1],
                        "wait_range": pattern[2]
                    }
                else:
                    pattern_config = {
                        "key": pattern[0],
                        "mode": "Custom",
                        "hold": pattern[1],
                        "wait": pattern[2]
                    }
                patterns_config.append(pattern_config)
            
            # Create pattern configuration
            pattern_config = {
                "patterns": patterns_config,
                "pattern_hotkey": self.pattern_hotkey
            }
            
            # Save to file
            filepath = os.path.join("saves/patterns", f"{name}.json")
            if os.path.exists(filepath):
                reply = QMessageBox.question(self, "Confirm Overwrite",
                                          f"Pattern configuration '{name}' already exists. Overwrite?",
                                          QMessageBox.StandardButton.Yes | 
                                          QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    return

            try:
                # Ensure the saves directory exists right before writing
                os.makedirs("saves/patterns", exist_ok=True)
                with open(filepath, 'w') as f:
                    json.dump(pattern_config, f, indent=4)
                QMessageBox.information(self, "Success", 
                                     f"Pattern configuration saved as '{name}'")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                                   f"Failed to save pattern configuration: {str(e)}")

    def manage_saves(self, config_type="both"):
        if not os.path.exists("saves"):
            os.makedirs("saves")
            
        # Create a custom dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Load Configuration")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)

        # Add configuration type selector
        type_group = QGroupBox("Configuration Type")
        type_layout = QHBoxLayout()
        
        constant_radio = QRadioButton("Constant Key")
        pattern_radio = QRadioButton("Pattern")
        
        # Set the initial selection based on config_type
        if config_type == "constant":
            constant_radio.setChecked(True)
        elif config_type == "pattern":
            pattern_radio.setChecked(True)
        else:
            constant_radio.setChecked(True)  # Default to constant
            
        type_layout.addWidget(constant_radio)
        type_layout.addWidget(pattern_radio)
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Create list widget and buttons first
        list_widget = QListWidget()
        layout.addWidget(list_widget)

        # Button layout
        button_layout = QHBoxLayout()
        
        # Load button
        load_btn = QPushButton("Load")
        load_btn.setEnabled(False)  # Initially disabled
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setEnabled(False)  # Initially disabled
        
        # Close button
        close_btn = QPushButton("Close")
        
        button_layout.addWidget(load_btn)
        button_layout.addWidget(delete_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        def update_list():
            list_widget.clear()
            save_files = []
            save_names = []
            
            try:
                directory = "saves/constant" if constant_radio.isChecked() else "saves/patterns"
                if os.path.exists(directory):
                    save_files = [f for f in os.listdir(directory) if f.endswith(".json")]
                    save_names = [os.path.splitext(f)[0] for f in save_files]
            except Exception as e:
                QMessageBox.warning(dialog, "Warning", 
                                 f"Failed to list configurations: {str(e)}")

            for name in save_names:
                item = QListWidgetItem(name)
                list_widget.addItem(item)
                
            # Update button states
            has_items = list_widget.count() > 0
            load_btn.setEnabled(has_items)
            delete_btn.setEnabled(has_items)

        # Connect radio buttons
        constant_radio.toggled.connect(update_list)
        pattern_radio.toggled.connect(update_list)
        
        # Initial list update
        update_list()
        
        # The buttons have already been created and added to the layout above
        # We just need to connect their signals

        def delete_selected():
            current_item = list_widget.currentItem()
            if not current_item:
                return
                
            name = current_item.text()
            reply = QMessageBox.question(dialog, "Confirm Delete",
                                      f"Are you sure you want to delete '{name}'?",
                                      QMessageBox.StandardButton.Yes | 
                                      QMessageBox.StandardButton.No)
                                      
            if reply == QMessageBox.StandardButton.Yes:
                config_type = "constant" if constant_radio.isChecked() else "pattern"
                directory = "saves/constant" if config_type == "constant" else "saves/patterns"
                filepath = os.path.join(directory, f"{name}.json")
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        list_widget.takeItem(list_widget.row(current_item))
                        
                        # Disable buttons if no items left
                        has_items = list_widget.count() > 0
                        load_btn.setEnabled(has_items)
                        delete_btn.setEnabled(has_items)
                        
                        QMessageBox.information(dialog, "Success", 
                                            f"{config_type.title()} configuration '{name}' deleted successfully")
                    else:
                        QMessageBox.warning(dialog, "Warning", 
                                         f"Configuration file '{name}.json' not found")
                except Exception as e:
                    QMessageBox.critical(dialog, "Error", 
                                      f"Failed to delete configuration: {str(e)}")

        def load_selected():
            current_item = list_widget.currentItem()
            if not current_item:
                return
                
            name = current_item.text()
            config_type = "constant" if constant_radio.isChecked() else "pattern"
            dialog.accept()
            self._load_configuration(name, config_type)

        # Connect buttons
        load_btn.clicked.connect(load_selected)
        delete_btn.clicked.connect(delete_selected)
        close_btn.clicked.connect(dialog.reject)
        
        # Double click to load
        list_widget.itemDoubleClicked.connect(lambda item: load_selected())
        
        dialog.exec()
        
    def _load_configuration(self, name, config_type):
        directory = "saves/constant" if config_type == "constant" else "saves/patterns"
        filepath = os.path.join(directory, f"{name}.json")
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            
            if config_type == "constant":
                # Load constant key settings
                if isinstance(config, dict):  # Direct constant key config
                    self.constant_key_input.setText(config["key"])
                    self.constant_hotkey = config.get("hotkey")
                else:
                    raise ValueError("Invalid constant key configuration format")
                    
                # Update hotkeys
                self.setup_global_hotkeys()
                
                QMessageBox.information(self, "Success", 
                                     f"Constant key configuration '{name}' loaded successfully")
                                     
            else:  # Pattern configuration
                # Clear existing patterns
                self.clear_all_patterns()
                
                # Load patterns
                if "patterns" in config:
                    for pattern in config["patterns"]:
                        key = pattern["key"]
                        mode = pattern["mode"]
                        
                        if mode == "Random":
                            # Set random mode values
                            self.random_radio.setChecked(True)
                            hold_range = pattern["hold_range"].split("-")
                            wait_range = pattern["wait_range"].split("-")
                            self.random_range.min_hold.setValue(float(hold_range[0]))
                            self.random_range.max_hold.setValue(float(hold_range[1]))
                            self.random_range.min_wait.setValue(float(wait_range[0]))
                            self.random_range.max_wait.setValue(float(wait_range[1]))
                        else:
                            # Set custom mode values
                            self.custom_radio.setChecked(True)
                            self.hold_input.value_spin.setValue(float(pattern["hold"]))
                            self.wait_input.value_spin.setValue(float(pattern["wait"]))
                            
                        # Set key and add pattern
                        self.key_input.setText(key)
                        self.add_pattern()
                
                # Load pattern hotkey
                if "pattern_hotkey" in config:
                    self.pattern_hotkey = config["pattern_hotkey"]
                    if self.pattern_hotkey:
                        self.pattern_hotkey_input.setText(self.pattern_hotkey)
                    
                # Update hotkeys
                self.setup_global_hotkeys()
                
                QMessageBox.information(self, "Success", 
                                     f"Pattern configuration '{name}' loaded successfully")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to load configuration: {str(e)}")

    def load_configuration(self, config_type="both"):
        self.manage_saves(config_type)
        
    def load_constant_key(self):
        self.load_configuration("constant")
        
    def load_pattern(self):
        self.load_configuration("pattern")
        
    def toggle_pattern(self):
        if self.is_pattern_active:
            self.stop_pattern()
        else:
            self.start_pattern()

    def initUI(self):
        self.setGeometry(300, 150, 600, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Title
        title_label = QLabel("Auto Key Holder")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)

        # Constant key section
        constant_key_group = QGroupBox("Constant Key Control")
        constant_key_layout = QVBoxLayout(constant_key_group)
        
        # Constant key input row
        key_input_layout = QHBoxLayout()
        key_input_layout.addWidget(QLabel("Key:"))
        self.constant_key_input = QLineEdit()
        self.constant_key_input.setPlaceholderText("Press Listen to capture key")
        self.constant_key_input.setReadOnly(True)
        self.constant_key_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        key_input_layout.addWidget(self.constant_key_input)
        
        # Listen button for constant key
        self.constant_listen_btn = QPushButton("Listen")
        self.constant_listen_btn.clicked.connect(lambda: self.start_listening(self.constant_key_input))
        key_input_layout.addWidget(self.constant_listen_btn)
        constant_key_layout.addLayout(key_input_layout)
        
        # Hotkey input for constant key
        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(QLabel("Hotkey:"))
        self.constant_hotkey_input = QLineEdit()
        self.constant_hotkey_input.setPlaceholderText("Press Listen to set hotkey")
        self.constant_hotkey_input.setReadOnly(True)
        self.constant_hotkey_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hotkey_layout.addWidget(self.constant_hotkey_input)
        
        # Listen button for hotkey
        self.constant_hotkey_listen = QPushButton("Listen")
        self.constant_hotkey_listen.clicked.connect(lambda: self.start_listening(self.constant_hotkey_input, True))
        hotkey_layout.addWidget(self.constant_hotkey_listen)
        constant_key_layout.addLayout(hotkey_layout)
        
        # Constant key control buttons
        constant_key_buttons = QHBoxLayout()
        self.constant_key_start = QPushButton("Start Holding")
        self.constant_key_start.clicked.connect(self.toggle_constant_key)
        constant_key_buttons.addWidget(self.constant_key_start)
        constant_key_layout.addLayout(constant_key_buttons)
        
        # Save/Load buttons for constant key
        save_load_layout = QHBoxLayout()
        save_button = QPushButton("Save Constant Key")
        save_button.clicked.connect(self.save_constant_key)
        load_button = QPushButton("Load Constant Key")
        load_button.clicked.connect(self.load_constant_key)
        save_load_layout.addWidget(save_button)
        save_load_layout.addWidget(load_button)
        constant_key_layout.addLayout(save_load_layout)
        
        layout.addWidget(constant_key_group)

        # Pattern input section
        input_group = QGroupBox("Add New Pattern")
        input_layout = QVBoxLayout(input_group)

        # Key input for patterns
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Pattern Key:"))
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Press Listen to capture key")
        self.key_input.setReadOnly(True)
        self.key_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_input.setMinimumWidth(100)
        key_layout.addWidget(self.key_input)
        
        # Listen button for pattern key
        self.pattern_listen_btn = QPushButton("Listen")
        self.pattern_listen_btn.clicked.connect(lambda: self.start_listening(self.key_input))
        key_layout.addWidget(self.pattern_listen_btn)
        input_layout.addLayout(key_layout)

        # Time inputs stacked widget
        self.time_stack = QStackedWidget()
        
        # Custom duration page
        custom_page = QWidget()
        custom_layout = QHBoxLayout(custom_page)
        self.hold_input = TimeInputGroup("Hold Duration")
        self.wait_input = TimeInputGroup("Wait Duration")
        custom_layout.addWidget(self.hold_input)
        custom_layout.addWidget(self.wait_input)
        self.time_stack.addWidget(custom_page)

        # Random duration page
        self.random_range = RandomRangeGroup("Random Durations")
        self.time_stack.addWidget(self.random_range)
        
        input_layout.addWidget(self.time_stack)

        # Duration mode selection
        mode_layout = QHBoxLayout()
        self.duration_group = QButtonGroup()
        self.custom_radio = QRadioButton("Custom Durations")
        self.random_radio = QRadioButton("Random Durations")
        self.custom_radio.setChecked(True)
        
        self.duration_group.addButton(self.custom_radio)
        self.duration_group.addButton(self.random_radio)
        
        mode_layout.addWidget(self.custom_radio)
        mode_layout.addWidget(self.random_radio)
        input_layout.addLayout(mode_layout)

        # Connect radio buttons to stack widget
        self.custom_radio.toggled.connect(lambda: self.time_stack.setCurrentIndex(0))
        self.random_radio.toggled.connect(lambda: self.time_stack.setCurrentIndex(1))

        # Add pattern button
        add_button = QPushButton("Add Pattern")
        add_button.clicked.connect(self.add_pattern)
        input_layout.addWidget(add_button)

        layout.addWidget(input_group)

        # Pattern list group
        list_group = QGroupBox("Patterns")
        list_layout = QVBoxLayout(list_group)
        
        # Scroll area for patterns
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)
        
        # Container for patterns
        self.pattern_container = QWidget()
        self.pattern_layout = QVBoxLayout(self.pattern_container)
        self.pattern_layout.setSpacing(5)
        self.pattern_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.pattern_container)
        list_layout.addWidget(scroll)

        # Clear All button
        clear_all_button = QPushButton("Clear All Patterns")
        clear_all_button.clicked.connect(self.clear_all_patterns)
        list_layout.addWidget(clear_all_button)
        
        layout.addWidget(list_group)

        # Control section
        control_group = QGroupBox("Execution Controls")
        control_layout = QVBoxLayout(control_group)
        
        # Hotkey input for pattern control
        pattern_hotkey_layout = QHBoxLayout()
        pattern_hotkey_layout.addWidget(QLabel("Pattern Hotkey:"))
        self.pattern_hotkey_input = QLineEdit()
        self.pattern_hotkey_input.setPlaceholderText("Press Listen to set hotkey")
        self.pattern_hotkey_input.setReadOnly(True)
        self.pattern_hotkey_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pattern_hotkey_layout.addWidget(self.pattern_hotkey_input)
        
        # Listen button for pattern hotkey
        self.pattern_hotkey_listen = QPushButton("Listen")
        self.pattern_hotkey_listen.clicked.connect(lambda: self.start_listening(self.pattern_hotkey_input, True))
        pattern_hotkey_layout.addWidget(self.pattern_hotkey_listen)
        control_layout.addLayout(pattern_hotkey_layout)

        # Repetitions input
        rep_layout = QHBoxLayout()
        rep_layout.addWidget(QLabel("Repetitions:"))
        self.rep_input = QSpinBox()
        self.rep_input.setRange(-1, 999999)
        self.rep_input.setValue(-1)  # Set to infinite by default
        self.rep_input.setSpecialValueText("∞")  # Show infinity symbol for -1
        rep_layout.addWidget(self.rep_input)
        control_layout.addLayout(rep_layout)

        # Start/Stop buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start_pattern)
        button_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_pattern)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        control_layout.addLayout(button_layout)

        # Add save/load configuration buttons
        save_load_layout = QHBoxLayout()
        save_button = QPushButton("Save Pattern")
        save_button.clicked.connect(self.save_pattern)
        load_button = QPushButton("Load Pattern")
        load_button.clicked.connect(self.load_pattern)
        save_load_layout.addWidget(save_button)
        save_load_layout.addWidget(load_button)
        control_layout.addLayout(save_load_layout)

        layout.addWidget(control_group)

    def create_pattern_widget(self, pattern_num, pattern, is_random):
        # Create frame for the pattern
        frame = QFrame()
        frame.setFixedSize(540, 120)
        frame.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        frame.setLineWidth(1)
        
        main_layout = QVBoxLayout(frame)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Top row: Number, Key, Mode, and Buttons
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        
        # Pattern number
        num_label = QLabel(f"#{pattern_num}")
        num_label.setMinimumWidth(30)
        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_row.addWidget(num_label)
        
        # Key input with Listen button
        key_group = QGroupBox("Key")
        key_group.setMaximumHeight(60)
        key_layout = QHBoxLayout(key_group)
        key_layout.setContentsMargins(5, 2, 5, 2)
        key_layout.setSpacing(2)
        
        key_input = QLineEdit(pattern[0])
        key_input.setMinimumWidth(80)
        key_input.setMaximumWidth(200)
        key_input.setReadOnly(True)
        key_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        key_layout.addWidget(key_input)
        
        # Listen button inside key group
        listen_btn = QPushButton("Listen")
        listen_btn.setMaximumWidth(50)
        listen_btn.clicked.connect(lambda: self.start_listening(key_input))
        key_layout.addWidget(listen_btn)
        
        top_row.addWidget(key_group)
        
        # Mode selection
        mode_group = QGroupBox("Mode")
        mode_group.setMaximumHeight(60)
        mode_layout = QHBoxLayout(mode_group)
        mode_layout.setContentsMargins(5, 2, 5, 2)
        mode_combo = QComboBox()
        mode_combo.addItems(["Custom", "Random"])
        mode_combo.setCurrentText("Random" if is_random else "Custom")
        mode_layout.addWidget(mode_combo)
        top_row.addWidget(mode_group)

        # Buttons group
        button_group = QGroupBox()
        button_group.setMaximumHeight(60)
        button_layout = QHBoxLayout(button_group)
        button_layout.setContentsMargins(5, 2, 5, 2)
        button_layout.setSpacing(5)
        
        # Remove button in button group
        remove_btn = QPushButton("Remove")
        remove_btn.setMaximumWidth(70)
        remove_btn.clicked.connect(lambda: self.remove_pattern(frame))
        button_layout.addWidget(remove_btn)
        
        top_row.addWidget(button_group)
        main_layout.addLayout(top_row)

        # Duration inputs container
        duration_container = QWidget()
        duration_layout = QVBoxLayout(duration_container)
        duration_layout.setContentsMargins(0, 0, 0, 0)
        
        # Duration inputs stacked widget
        duration_stack = QStackedWidget()
        
        # Custom duration widget
        custom_widget = QWidget()
        custom_layout = QHBoxLayout(custom_widget)
        custom_layout.setContentsMargins(5, 5, 5, 5)
        
        # Hold duration
        hold_group = QGroupBox("Hold Duration")
        hold_layout = QHBoxLayout(hold_group)
        hold_layout.setContentsMargins(5, 2, 5, 2)
        hold_input = QDoubleSpinBox()
        hold_input.setRange(0.1, 9999.0)
        hold_input.setSingleStep(0.1)
        hold_input.setDecimals(1)
        hold_input.setValue(float(pattern[1]) if not is_random else 1.0)
        hold_input.setSuffix(" s")
        hold_layout.addWidget(hold_input)
        custom_layout.addWidget(hold_group)
        
        # Wait duration
        wait_group = QGroupBox("Wait Duration")
        wait_layout = QHBoxLayout(wait_group)
        wait_layout.setContentsMargins(5, 2, 5, 2)
        wait_input = QDoubleSpinBox()
        wait_input.setRange(0.0, 9999.0)
        wait_input.setSingleStep(0.1)
        wait_input.setDecimals(1)
        wait_input.setValue(float(pattern[2]) if not is_random else 0.0)
        wait_input.setSuffix(" s")
        wait_layout.addWidget(wait_input)
        custom_layout.addWidget(wait_group)
        
        duration_stack.addWidget(custom_widget)
        
        # Random duration widget
        random_widget = QWidget()
        random_layout = QHBoxLayout(random_widget)
        random_layout.setContentsMargins(5, 5, 5, 5)
        
        # Initialize ranges with defaults
        hold_range = ['0.1', '1.0']
        wait_range = ['0.0', '1.0']
        
        # Parse ranges if random mode
        if is_random:
            try:
                if isinstance(pattern[1], str):
                    parts = str(pattern[1]).strip().split('-')
                    if len(parts) == 2:
                        hold_range = [p.strip() for p in parts]
                if isinstance(pattern[2], str):
                    parts = str(pattern[2]).strip().split('-')
                    if len(parts) == 2:
                        wait_range = [p.strip() for p in parts]
            except Exception as e:
                print(f"Error parsing ranges: {e}")
                pass
        
        # Hold range
        hold_range_group = QGroupBox("Hold Range (Equal values = Fixed time)")
        hold_range_layout = QHBoxLayout(hold_range_group)
        hold_range_layout.setContentsMargins(5, 2, 5, 2)
        
        min_hold = QDoubleSpinBox()
        min_hold.setRange(0.1, 9999.0)
        min_hold.setSingleStep(0.1)
        min_hold.setDecimals(1)
        min_hold.setValue(float(hold_range[0]))
        min_hold.setSuffix(" s")
        
        max_hold = QDoubleSpinBox()
        max_hold.setRange(0.1, 9999.0)
        max_hold.setSingleStep(0.1)
        max_hold.setDecimals(1)
        max_hold.setValue(float(hold_range[1]))
        max_hold.setSuffix(" s")
        
        # Add tooltip to explain the behavior
        tooltip = "If min and max are equal, this time will be used exactly (no randomization)"
        min_hold.setToolTip(tooltip)
        max_hold.setToolTip(tooltip)
        
        hold_range_layout.addWidget(min_hold)
        hold_range_layout.addWidget(QLabel("-"))
        hold_range_layout.addWidget(max_hold)
        random_layout.addWidget(hold_range_group)
        
        # Wait range
        wait_range_group = QGroupBox("Wait Range (Equal values = Fixed time)")
        wait_range_layout = QHBoxLayout(wait_range_group)
        wait_range_layout.setContentsMargins(5, 2, 5, 2)
        
        min_wait = QDoubleSpinBox()
        min_wait.setRange(0.0, 9999.0)
        min_wait.setSingleStep(0.1)
        min_wait.setDecimals(1)
        min_wait.setValue(float(wait_range[0]))
        min_wait.setSuffix(" s")
        
        max_wait = QDoubleSpinBox()
        max_wait.setRange(0.0, 9999.0)
        max_wait.setSingleStep(0.1)
        max_wait.setDecimals(1)
        max_wait.setValue(float(wait_range[1]))
        max_wait.setSuffix(" s")
        
        # Add tooltip to explain the behavior
        tooltip = "If min and max are equal, this time will be used exactly (no randomization)"
        min_wait.setToolTip(tooltip)
        max_wait.setToolTip(tooltip)
        
        wait_range_layout.addWidget(min_wait)
        wait_range_layout.addWidget(QLabel("-"))
        wait_range_layout.addWidget(max_wait)
        random_layout.addWidget(wait_range_group)
        
        duration_stack.addWidget(random_widget)
        duration_layout.addWidget(duration_stack)
        main_layout.addWidget(duration_container)
        
        # Connect mode combo to stack widget
        mode_combo.currentTextChanged.connect(
            lambda t: duration_stack.setCurrentIndex(1 if t == "Random" else 0)
        )
        duration_stack.setCurrentIndex(1 if is_random else 0)
        
        # Store references to inputs for updating
        frame.key_input = key_input
        frame.mode_combo = mode_combo
        frame.hold_input = hold_input
        frame.wait_input = wait_input
        frame.min_hold = min_hold
        frame.max_hold = max_hold
        frame.min_wait = min_wait
        frame.max_wait = max_wait
        
        # Connect value change signals for automatic updates
        key_input.textChanged.connect(lambda: self.update_pattern(frame))
        mode_combo.currentTextChanged.connect(lambda: self.update_pattern(frame))
        hold_input.valueChanged.connect(lambda: self.update_pattern(frame))
        wait_input.valueChanged.connect(lambda: self.update_pattern(frame))
        min_hold.valueChanged.connect(lambda: self.update_pattern(frame))
        max_hold.valueChanged.connect(lambda: self.update_pattern(frame))
        min_wait.valueChanged.connect(lambda: self.update_pattern(frame))
        max_wait.valueChanged.connect(lambda: self.update_pattern(frame))
        
        return frame

    def add_pattern(self):
        key = self.key_input.text().strip()
        if not key:
            return

        if self.random_radio.isChecked():
            # Store random ranges for this key
            self.random_ranges[key] = (
                self.random_range.min_hold.value(),
                self.random_range.max_hold.value(),
                self.random_range.min_wait.value(),
                self.random_range.max_wait.value()
            )
            pattern = (key, 
                      f"{self.random_range.min_hold.value()}-{self.random_range.max_hold.value()}", 
                      f"{self.random_range.min_wait.value()}-{self.random_range.max_wait.value()}")
        else:
            hold_duration = self.hold_input.value_spin.value()
            wait_duration = self.wait_input.value_spin.value()
            pattern = (key, str(hold_duration), str(wait_duration))

        self.patterns.append(pattern)
        
        # Create and add the pattern widget
        pattern_widget = self.create_pattern_widget(len(self.patterns), pattern, self.random_radio.isChecked())
        self.pattern_layout.addWidget(pattern_widget)
        
        self.key_input.clear()
        
        # Update start button state
        self.start_button.setEnabled(len(self.patterns) > 0)

    def remove_pattern(self, pattern_widget):
        # Find the index of the pattern widget
        index = -1
        for i in range(self.pattern_layout.count()):
            if self.pattern_layout.itemAt(i).widget() == pattern_widget:
                index = i
                break
                
        if index >= 0:
            # Remove from layout first
            self.pattern_layout.removeWidget(pattern_widget)
            # Remove the pattern data
            removed_pattern = self.patterns.pop(index)
            # Clean up random ranges if necessary
            if removed_pattern[0] in self.random_ranges:
                del self.random_ranges[removed_pattern[0]]
            
            # Delete the widget
            pattern_widget.deleteLater()
            
            # Update the numbers immediately
            self.update_pattern_numbers()
            
        # Update start button state
        self.start_button.setEnabled(len(self.patterns) > 0)
        
    def update_pattern_numbers(self):
        # First collect valid widgets
        valid_widgets = []
        for i in range(self.pattern_layout.count()):
            item = self.pattern_layout.itemAt(i)
            if item and item.widget():
                valid_widgets.append(item.widget())
        
        # Now update numbers for valid widgets
        for i, widget in enumerate(valid_widgets):
            # Get the main layout
            main_layout = widget.layout()
            if not main_layout:
                continue
                
            # Get the top row (first item)
            top_row_item = main_layout.itemAt(0)
            if not top_row_item or not isinstance(top_row_item, QHBoxLayout):
                continue
                
            # Get the number label (first widget in top row)
            num_label_item = top_row_item.itemAt(0)
            if not num_label_item:
                continue
                
            num_label = num_label_item.widget()
            if num_label and isinstance(num_label, QLabel):
                num_label.setText(f"#{i + 1}")
        
    def clear_all_patterns(self):
        # Remove all pattern widgets
        while self.pattern_layout.count() > 0:
            item = self.pattern_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Clear all patterns and random ranges
        self.patterns.clear()
        self.random_ranges.clear()
        
        # Update start button state
        self.start_button.setEnabled(False)
        
    def renumber_patterns(self):
        # For backward compatibility, just call update_pattern_numbers
        self.update_pattern_numbers()

    def toggle_constant_key(self):
        if not self.is_constant_key_active:
            # Start holding
            key = self.constant_key_input.text().strip()
            if not key:
                return
                
            self.constant_key_thread = ConstantKeyThread(key)
            self.constant_key_thread.start()
            self.is_constant_key_active = True
            self.constant_key_start.setText("Stop Holding")
            self.constant_key_input.setEnabled(False)
            self.constant_listen_btn.setEnabled(False)
        else:
            # Stop holding
            if self.constant_key_thread:
                self.constant_key_thread.stop()
                self.constant_key_thread.wait()  # Wait for thread to finish
                self.constant_key_thread = None
            self.is_constant_key_active = False
            self.constant_key_start.setText("Start Holding")
            self.constant_key_input.setEnabled(True)
            self.constant_listen_btn.setEnabled(True)
            # Reapply hotkeys after stopping
            self.setup_global_hotkeys()

    def start_pattern(self):
        if not self.patterns:
            return
            
        if self.pattern_thread and self.pattern_thread.is_running():
            return

        # Save the current state of hotkeys
        saved_constant_hotkey = self.constant_hotkey
        saved_pattern_hotkey = self.pattern_hotkey

        self.pattern_thread = KeyHolderThread(
            self.patterns,
            self.random_radio.isChecked(),
            self.rep_input.value(),
            self.random_ranges
        )
        self.pattern_thread.pattern_complete.connect(self.on_pattern_complete)
        self.pattern_thread.start()

        self.is_pattern_active = True
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Reapply hotkeys to ensure they work while pattern is running
        self.constant_hotkey = saved_constant_hotkey
        self.pattern_hotkey = saved_pattern_hotkey
        self.setup_global_hotkeys()
        self.stop_button.setEnabled(True)

    def stop_pattern(self):
        if self.pattern_thread and self.pattern_thread.is_running():
            self.pattern_thread.running = False
            self.pattern_thread.stop()
            self.pattern_thread.wait()
            # Ensure all keys are released
            for pattern in self.patterns:
                try:
                    keyboard.release(pattern[0])
                except:
                    pass
        self.is_pattern_active = False
        self.on_pattern_complete()

    def on_pattern_complete(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.is_pattern_active = False
        
    def update_pattern(self, frame):
        # Find the index of the pattern
        index = -1
        for i in range(self.pattern_layout.count()):
            if self.pattern_layout.itemAt(i).widget() == frame:
                index = i
                break
                
        if index >= 0:
            key = frame.key_input.text().strip()
            if not key:
                return
                
            is_random = frame.mode_combo.currentText() == "Random"
            
            if is_random:
                # Update random ranges
                self.random_ranges[key] = (
                    frame.min_hold.value(),
                    frame.max_hold.value(),
                    frame.min_wait.value(),
                    frame.max_wait.value()
                )
                pattern = (key,
                          f"{frame.min_hold.value()}-{frame.max_hold.value()}",
                          f"{frame.min_wait.value()}-{frame.max_wait.value()}")
            else:
                # Remove from random ranges if it was previously random
                if key in self.random_ranges:
                    del self.random_ranges[key]
                pattern = (key, str(frame.hold_input.value()), str(frame.wait_input.value()))
            
            # Update the pattern in the list
            self.patterns[index] = pattern

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AutoKeyHolder()
    window.show()
    sys.exit(app.exec())
