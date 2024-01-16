# The game is a text based adventure that randomly generates rooms and items. There are locks for some rooms that
# prevent advancement without the proper item.
#
#
# Ver.      Date          Author
# 2.0   Jan 11, 2024    Robertp3001

import json
import os
import random
import time


class Room:
    def __init__(self, room_name, room_description, saved_connection=None, saved_lock_item=None, saved_item=None):
        if saved_connection is None:
            saved_connection = [None, None, None, None, None, None]
        self.room_name = room_name
        self.room_description = room_description
        self.rooms_connected = saved_connection
        self.room_fixtures = None
        self.room_lock_item = saved_lock_item
        self.room_items_contained = saved_item
        self.room_tier = 0

    # Future Use
    def get_color_room_name(self):
        return self.room_name

    # Future Use
    def create_fixtures(self, room_fixtures):
        self.room_fixtures = room_fixtures

    def create_lock(self, room_lock_item):
        self.room_lock_item = room_lock_item

    def place_items(self, room_items_contained):
        self.room_items_contained = room_items_contained


class Item:
    def __init__(self, item_name, item_description):
        self.item_name = item_name
        self.item_description = item_description

    def get_color_item_name(self):
        return self.item_name


class Player:
    def __init__(self, player_name, oxygen_level, inventory=None, current_room=None, direction_facing=0):
        if inventory is None:
            inventory = []
        self.current_room = current_room
        self.player_name = player_name
        self.direction_facing = direction_facing
        self.oxygen_level = oxygen_level
        self.inventory = inventory

    def move_rooms(self, command):
        room_number = 7
        for direction in game.settings["directions"]:
            if command in direction:
                room_number = game.settings["directions"].index(direction)
                break
        if room_number == 7:
            print_slower("Invalid Direction Input")
            return
        room_number = self.new_facing()[room_number]
        connected_room = self.current_room.rooms_connected[room_number]

        if room_number < 4:
            self.direction_facing = room_number

        if connected_room is None:
            print_slower("There's no room there")
            return

        if connected_room.room_lock_item:
            print_slower(connected_room.room_name + " is locked with " + connected_room.room_lock_item.item_name)
            for item in self.inventory:
                if item == connected_room.room_lock_item:
                    print_slower(connected_room.room_name + " unlocked with " + item.item_name)
                    connected_room.room_lock_item = None
                    self.current_room = connected_room
                    break
            return

        self.current_room = connected_room
        return

    def search_room(self):
        turning_directions = self.new_facing()
        new_rooms = [None, None, None, None, None, None]
        print_slower("Doors:")
        for i in range(0, 6):
            new_rooms[i] = self.current_room.rooms_connected[turning_directions[i]]

        new_room_names = []
        for i in range(0, 6):
            if new_rooms[i] is not None:
                new_room_names.append(game.settings["directions"][i].capitalize() + ": " + new_rooms[i].room_name)
        print_slower("  -" + ", ".join(new_room_names))
        if self.current_room.room_items_contained:
            print_slower("Items contained: " + self.current_room.room_items_contained.get_color_item_name() +
                         "\n  -" + self.current_room.room_items_contained.item_description)

    def get_items(self, command):
        if not self.current_room.room_items_contained:
            print_slower("There is no item here.")
            return

        if command.lower() in self.current_room.room_items_contained.item_name.lower():
            print_slower(self.current_room.room_items_contained.item_name + " obtained.")
            self.inventory.append(self.current_room.room_items_contained)
            self.current_room.room_items_contained = None
            return

        print_slower(command.capitalize() + " was not found.")

    def show_inventory(self):
        if self.inventory:
            print_slower("Inventory:")
            item_name = []
            for item in self.inventory:
                item_name.append(item.item_name)
            print_slower("  -" + ", ".join(item_name))

    def new_facing(self):
        all_directions = []
        for i in range(0, 4):
            all_directions.append((i + self.direction_facing) % 4)
        for i in range(4, 6):
            all_directions.append(i)
        return all_directions


class Game:
    def __init__(self):
        self.game_loaded = False
        self.final_room = None
        self.keys = None
        self.player = None
        self.rooms = None
        self.items = None
        self.settings = None
        self.file_path = None
        self.reset()

    def reset(self):
        self.file_path = 'Settings.json'
        self.settings = import_settings(self.file_path)
        self.items = self.create_items()
        self.rooms = self.create_rooms()
        self.player = self.create_player()
        self.keys = None
        self.final_room = None
        self.game_loaded = False

    def main_menu(self):
        while True:
            print_slower("Welcome " + self.settings["player_name"] + "!")
            print_slower("Enter New Game, Load Game, ", '')
            if self.game_loaded:
                print_slower("Resume Game, ", '')
            print_slower("Settings, Quit:")
            command = input(">>>").lower()
            if command == "new game":
                self.new_game()
            elif command == "resume game" and self.game_loaded:
                self.resume_game()
            elif command == "load game":
                self.load()
            elif command == "settings":
                self.settings_menu()
            elif command == "quit":
                break
            else:
                print_slower("Invalid Command")

    def play(self):
        while True:
            self.ui_display()
            command = input("Enter Command:\n>>>").strip().lower()
            self.print_break()

            if len(command) < 3:
                print_slower("Invalid Command.")
                continue
            elif command.startswith(self.settings["player_commands"]["move"]):
                self.player.move_rooms(command[len(self.settings["player_commands"]["move"]):].strip())
            elif command.startswith(self.settings["player_commands"]["grab"]):
                self.player.get_items(command[len(self.settings["player_commands"]["grab"]):].strip())
            elif self.settings["player_commands"]["search"].startswith(command):
                self.player.search_room()
            elif command in self.settings["player_commands"]["inventory"]:
                self.player.show_inventory()
            elif command in self.settings["player_commands"]["help"]:
                self.help()
            elif command in self.settings["player_commands"]["save"]:
                self.save_game()
            elif command in self.settings["player_commands"]["quit"]:
                break
            else:
                print_slower("Invalid Command.")
                continue

            if self.player.current_room == self.final_room:
                self.final_encounter()
                break

    def new_game(self):
        self.reset()
        if self.error_check():
            return
        self.settings["player_name"] = input("Enter player name:\n>>>")
        self.random_select()
        self.store_items()
        self.connect_rooms()
        self.lock_rooms()
        print_slower(self.settings["scenes"]["opening_scene"] + "\n")
        self.play()

    def ui_display(self):
        if self.player.current_room is not None:
            print_slower("Current room: " + self.player.current_room.room_name)
            print_slower("  -" + self.player.current_room.room_description)
            self.player.search_room()

    def save_game(self):
        save_file = {"final_room": self.settings["final_room"],
                     "text_speed": self.settings["text_speed"],
                     "player_name": self.settings["player_name"],
                     "oxygen_level": self.settings["oxygen_level"],
                     "file_name": self.settings["file_name"],
                     "current_room": self.player.current_room.room_name,
                     "direction_facing": self.player.direction_facing,
                     "player_commands": self.settings["player_commands"],
                     "directions": self.settings["directions"],
                     "scenes": self.settings["scenes"]
                     }

        player_inventory = []
        if self.player.inventory:
            for item in self.player.inventory:
                player_inventory.append(item.item_name)
        save_file["inventory"] = player_inventory

        saved_rooms = []
        for room in self.rooms:
            saved_connections = []
            saved_item = None
            saved_lock = None
            for connection in room.rooms_connected:
                if connection:
                    saved_connections.append(connection.room_name)
                else:
                    saved_connections.append(None)
            if room.room_lock_item:
                saved_lock = room.room_lock_item.item_name
            if room.room_items_contained:
                saved_item = room.room_items_contained.item_name
            saved_rooms.append([room.room_name,
                                room.room_description,
                                saved_connections,
                                saved_lock,
                                saved_item])
        save_file["rooms"] = saved_rooms

        if self.settings["file_name"] == "":
            save_file["file_name"] = "Save Files\\" + self.settings["player_name"] + ".json"
        with open(save_file["file_name"], 'w') as file:
            json.dump(save_file, file, indent=4)
        print_slower("---Game Saved---")

    def load(self):
        save_file_path = "./Save Files"
        save_files = [f for f in os.listdir(save_file_path) if f.endswith(".json")]

        print_slower("Save Files:")
        for file in save_files:
            print_slower(file[:-5])
        file_loaded = input("Enter File name:\n>>>") + ".json"
        if file_loaded in save_files:
            self.settings = import_settings(self.file_path)
            self.items = self.create_items()
            self.rooms = self.create_rooms()
            self.player = self.create_player()
            self.settings = import_settings("Save Files\\" + file_loaded)

            new_room_list = []
            for save_room in self.settings["rooms"]:
                for room in self.rooms:
                    if room.room_name == save_room[0]:
                        room.room_lock_item = find_item(self.items, save_room[3])
                        room.room_items_contained = find_item(self.items, save_room[4])
                        for i in range(0, 6):
                            if save_room[2][i]:
                                room.rooms_connected[i] = find_room(self.rooms, save_room[2][i])
                        new_room_list.append(room)
            self.rooms = new_room_list
            self.player.current_room = find_room(self.rooms, self.settings["current_room"])
            self.player.direction_facing = self.settings["direction_facing"]
            for item_name in self.settings["inventory"]:
                self.player.inventory.append(find_item(self.items, item_name))
            self.final_room = find_room(self.rooms, self.settings["final_room"])
            self.game_loaded = True
            self.resume_game()
        else:
            print_slower("File not found.")

    def resume_game(self):
        self.play()

    @staticmethod
    def print_break():
        print_slower("-" * 100)

    def final_encounter(self):
        print_slower(self.settings["scenes"]["final_scene"])

    def help(self):
        print_slower("Commands: ", '')
        print_slower(", ".join(list(self.settings["player_commands"].values())))
        return

    # Just checking the start values won't bomb the code.
    def error_check(self):
        if self.settings["room_count"] == 0:
            print_slower("Not enough rooms. Can not have 0 rooms.")
            return True

        if self.settings["room_count"] > len(self.rooms):
            print_slower("Too many rooms. I don't have that many made.")
            return True

        if self.settings["item_count"] > len(self.items):
            print_slower("Too many items. I don't have that many to pick from.")
            return True

        if self.settings["room_count"] <= self.settings["item_count"] + 1:
            print_slower("Too many items. Can not have more items than rooms excluding first and last room.")
            return True

        if self.settings["key_count"] > self.settings["item_count"]:
            print_slower("Too many keys. Can not have more keys than items.")
            return True

        if self.settings["key_count"] == 0:
            print_slower("Not enough keys. Min. 1")
            return True
        return False

    def settings_menu(self):
        while True:
            print_slower("You can change number of rooms, items, and keys. You can also change the final room, "
                         "print speed.")
            for key, item in self.settings.items():
                if key != "rooms" and key != "game_items" and key != "scenes":
                    print_slower(key + ":" + str(item))
            change = input("Enter settings:")
            if change == "quit":
                return
            split_change = change.split(":")

            if split_change[0] == ("room_count" or "item_count" or "key_count" or "oxygen_level"):
                split_change[1] = int(split_change[1])
            elif split_change[0] == "text_speed":
                split_change[1] = float(split_change[1])

            if split_change[0] in self.settings.keys():
                self.settings[split_change[0]] = split_change[1]
                print_slower(split_change[0] + " set to " + str(split_change[1]))

    def lock_rooms(self):
        for room in self.rooms:
            if room.room_tier != 1:
                room.create_lock(self.keys[room.room_tier - 2])

    # Creates lists of random rooms, items, and keys. Removed keys from items.
    # I might just create a separate key list in the json.
    def random_select(self):
        self.final_room = find_room(self.rooms, self.settings["final_room"])
        self.rooms.remove(self.final_room)
        self.rooms = random.sample(self.rooms, self.settings["room_count"])
        self.player.current_room = random.choice(self.rooms)
        self.items = random.sample(self.items, self.settings["item_count"])
        self.keys = list(random.sample(self.items, self.settings["key_count"]))
        for key in self.keys:
            self.items.remove(key)

    # This will store all the items and keys while assigning tier levels for every room.
    def store_items(self):
        selected_rooms = list(self.rooms)  # Grabs all rooms
        selected_rooms.remove(self.player.current_room)  # Removes the starting room
        selected_rooms = random.sample(selected_rooms, self.settings["item_count"])  # Select rooms equal to items

        self.player.current_room.room_tier = 1  # Sets start room as the first tier
        self.final_room.room_tier = self.settings["key_count"] + 1
        # This loop will ensure there is at least one key for each tier
        tier_number = 0  # Tier Number is zero for proper selection in the list
        while tier_number < len(self.keys):
            room = random.choice(selected_rooms)  # Randomly select a room
            room.room_tier = tier_number + 1  # Adds the current tier to it
            if tier_number != len(self.keys):  # Places keys for next tier in the current tier except for final room.
                room.place_items(self.keys[tier_number])
            tier_number += 1  # Goes to next tier
            selected_rooms.remove(room)  # Removes the room from the list so that random selection doesn't choose again.

        # Places all non-key items
        for room, item in zip(selected_rooms, self.items):  # Combines the rooms and items
            room.place_items(item)  # Adds item to each instance of room

        # This just randomly selects a tier number for all rooms.
        for room in self.rooms:
            if room.room_tier == 0:
                room.room_tier = random.randint(1, len(self.keys))

    # This will connect rooms to each other. Building from tier 1 rooms to the final room.
    def connect_rooms(self):
        tier_number = 1
        self.rooms.append(self.final_room)
        connected_rooms = list([self.player.current_room])
        remaining_rooms = list(self.rooms)
        remaining_rooms.remove(self.player.current_room)
        while tier_number <= self.settings["key_count"] + 1:
            rooms = []
            for room in remaining_rooms:  # Create a list of all rooms for current tier
                if room.room_tier == tier_number:
                    rooms.append(room)
            for room in rooms:  # Cycle through list to connect to rooms that have connections
                room2, connection_direction = self.find_connection(connected_rooms)
                room2.rooms_connected[connection_direction] = room
                room.rooms_connected[self.opposite_room(connection_direction)] = room2
                connected_rooms.append(room)
                remaining_rooms.remove(room)
            tier_number += 1

    # Will just find the opposite room based on a given word
    @staticmethod
    def opposite_room(direction_value):
        if direction_value < 4:
            direction_value = (direction_value + 2) % 4
        elif direction_value % 2 == 0:
            direction_value += 1
        else:
            direction_value -= 1
        return direction_value

    # This will select a room and one of its connection points as long as that point is None
    @staticmethod
    def find_connection(connected_rooms):
        while True:
            room2 = random.choice(connected_rooms)
            connection_points = []
            for i in range(0, 6):
                if room2.rooms_connected[i] is None:
                    connection_points.append(i)
            if connection_points:
                return room2, random.choice(connection_points)

    def create_items(self):
        item_list = []
        for items in self.settings['game_items']:
            item_list.append(Item(*items))
        return item_list

    def create_rooms(self):
        room_list = []
        for rooms in self.settings['rooms']:
            room_list.append(Room(*rooms))
        return room_list

    def create_player(self):
        return Player(self.settings["player_name"], self.settings["oxygen_level"])


def find_item(item_list, item_name):
    for item in item_list:
        if item.item_name == item_name:
            return item
    return None


def find_room(room_list, room_name):
    for room in room_list:
        if room.room_name == room_name:
            return room
    return None


def import_settings(settings_file):
    with open(settings_file, 'r') as file:
        settings = json.load(file)
    return settings


def print_slower(text_output, ending='\n'):
    letter_counter = 0
    letter_number = 0
    while letter_number < len(text_output):
        if (letter_counter >= 120 and text_output[letter_number] == " ") or text_output[letter_number] == '\n':
            print('')
            letter_counter = 0
            letter_number += 1
        elif text_output[letter_number] == '\033':
            # Handle ANSI escape code
            start = letter_number
            letter_number += 1
            while letter_number < len(text_output) and text_output[letter_number] not in ('m', 'H', 'J', 'K'):
                letter_number += 1
            # Print the entire escape code without delay
            print(text_output[start:letter_number + 1], end='', flush=True)
            letter_number += 1  # Skip the last character of the escape code
        else:
            print(text_output[letter_number], end="", flush=True)
            letter_number += 1
            letter_counter += 1
            time.sleep(game.settings['text_speed'])
    print(ending, end='')


if __name__ == '__main__':
    game = Game()
    game.main_menu()
