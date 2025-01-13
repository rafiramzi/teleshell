from telethon import TelegramClient, events
from tabulate import tabulate 
import pygame
import curses
from datetime import datetime
from playsound import playsound
import asyncio
import subprocess
import os

pygame.mixer.init()
# Replace with your API credentials
api_id = 20883957
api_hash = 'f063432604174518040df08343efec65'

# Create a Telegram client instance
client = TelegramClient('TeleShell', api_id, api_hash)
def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

 # Import the tabulate library

def play_notification():
    """Play a notification sound."""
    try:
        pygame.mixer.music.load("notification/notif.mp3")
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Failed to play sound: {e}")

async def fetch_contacts():
    """Fetch and display the user's contacts."""
    clear_screen()
    try:
        print("\nFetching contacts...")
        dialogs = await client.get_dialogs()
        contacts = [
            {
                "id": dialog.entity.id,
                "name": f"{dialog.entity.first_name or ''} {dialog.entity.last_name or ''}".strip(),
                "username": dialog.entity.username or "N/A",
                "phone": dialog.entity.phone or "N/A"
            }
            for dialog in dialogs if dialog.is_user and dialog.entity.bot is False
        ]

        if not contacts:
            print("No contacts found.")
        else:
            print("\nContacts:")
            table = [[contact["id"],contact["name"], contact["username"], contact["phone"]] for contact in contacts]
            headers = ["Contact Id","Name", "Username", "Phone Number"]
            print(tabulate(table, headers=headers, tablefmt="double_grid"))
    except Exception as e:
        print(f"Error fetching contacts: {e}")


import curses

async def select_contact(contacts):
    """Display a curses-based menu to select a contact with scrollable functionality."""
    selected_contact = None

    def draw_menu(stdscr):
        nonlocal selected_contact
        curses.curs_set(0)

        selected_idx = 0  # Currently selected item index
        top_idx = 0  # Top index of the visible portion of the list
        max_visible = curses.LINES - 4  # Number of items that fit on the screen

        while True:
            curses.update_lines_cols()  # Update terminal dimensions dynamically
            max_width = curses.COLS - 4  # Leave padding for borders
            stdscr.clear()
            stdscr.addstr(0, 0, "Use ↑ ↓ to navigate, Enter to select, or 'q' to cancel.\n", curses.A_BOLD)

            # Calculate visible contacts
            visible_contacts = contacts[top_idx:top_idx + max_visible]

            for idx, contact in enumerate(visible_contacts):
                display_name = f"{contact['name']} ({contact['username'] or contact['phone']})"
                display_name = (display_name[:max_width - 3] + '...') if len(display_name) > max_width else display_name
                contact_display_idx = idx + 2  # Offset for header
                if idx + top_idx == selected_idx:
                    stdscr.addstr(contact_display_idx, 0, f"> {display_name}", curses.A_REVERSE)
                else:
                    stdscr.addstr(contact_display_idx, 0, f"  {display_name}")

            stdscr.refresh()
            key = stdscr.getch()

            if key == curses.KEY_UP:
                selected_idx = (selected_idx - 1) % len(contacts)
                if selected_idx < top_idx:
                    top_idx -= 1  # Scroll up
            elif key == curses.KEY_DOWN:
                selected_idx = (selected_idx + 1) % len(contacts)
                if selected_idx >= top_idx + max_visible:
                    top_idx += 1  # Scroll down
            elif key == curses.KEY_ENTER or key in [10, 13]:  # Enter key
                selected_contact = contacts[selected_idx]
                break
            elif key == ord('q'):
                break

        stdscr.clear()
        stdscr.refresh()

    curses.wrapper(draw_menu)
    return selected_contact



async def send_message():
    try:
        clear_screen()
        print("Fetching contacts for selection...")
        dialogs = await client.get_dialogs()
        contacts = [
            {
                "id": dialog.entity.id,
                "name": f"{dialog.entity.first_name or ''} {dialog.entity.last_name or ''}".strip(),
                "username": dialog.entity.username or "N/A",
                "phone": dialog.entity.phone or "N/A"
            }
            for dialog in dialogs if dialog.is_user and dialog.entity.bot is False
        ]

        if not contacts:
            print("No contacts available.")
            return

        selected_contact = await select_contact(contacts)
        if not selected_contact:
            print("No contact selected. Returning to main menu.")
            return

        user = await client.get_entity(selected_contact['id'])
        clear_screen()
        print(f"{user.first_name or ''} {user.last_name or ''} ({user.phone or 'N/A'}) [Room]")
        print("Type (/\quit) to exit the room chat")

        last_sent_time = datetime.utcnow()

        async def listen_for_replies():
            nonlocal last_sent_time
            async for event in client.iter_messages(user, from_user=user):
                event_date_naive = event.date.replace(tzinfo=None)
                if event_date_naive > last_sent_time:
                    print(f"\n[{user.first_name or ''}]: {event.text}")
                    play_notification()

        client.loop.create_task(listen_for_replies())

        
        while True:
            message = input("\n[You]: ")
            if message.strip() == "/\\quit":
                print("Exiting the conversation...")
                break
            last_sent_time = datetime.utcnow()
            await client.send_message(user, message)
            await listen_for_replies()

            reply_received = False
            while not reply_received:
                async for event in client.iter_messages(user, from_user=user,):
                    if event.date.replace(tzinfo=None) > last_sent_time:
                        print(f"\n[{user.first_name or ''}]: {event.text}")
                        play_notification()
                        reply_received = True

    except Exception as e:
        print(f"Failed to send message: {e}")





async def show_profile_details():
    clear_screen()
    """Show the logged-in user's profile details."""
    try:
        me = await client.get_me()
        print("\nYour Profile Details:")
        print(f"Name: {me.first_name} {me.last_name or ''}")
        print(f"Username: {me.username or 'N/A'}")
        print(f"Phone: {me.phone or 'N/A'}")
    except Exception as e:
        print(f"Error fetching profile details: {e}")

async def main():
    """Main function with a menu to choose options."""
    await client.start()
    clear_screen()
    print("Login successful!")
    me = await client.get_me()

    banner = """
 _____ ___  __   ___   ___  _ __ ___  __   __
/_  _// _/ / /  / _/ ,' _/ /// // _/ / /  / /
 / / / _/ / /_ / _/ _\ `. / ` // _/ / /_ / /_
/_/ /___//___//___//___,'/_n_//___//___//___/
Just a Telegram, but in a nutshell
"""

    print(banner)
    while True:
        print(f"Welcome, {me.first_name} {me.last_name}")
        print("\n==========================")
        print("[1] Fetch contacts")
        print("[2] Send message")
        print("[3] Your profile details")
        print("[4] Exit")
        print("==========================")
        
        choice = input("Choose an option: ")
        
        if choice == "1":
            await fetch_contacts()
        elif choice == "2":
            await send_message()
        elif choice == "3":
            await show_profile_details()
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

# Run the main menu
with client:
    client.loop.run_until_complete(main())

