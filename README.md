# Trump Truth Social Archiver & Popularity Tracker

This project is a Python-based tool designed to archive and analyse posts from Donald Trump's Truth Social account

This  program fetches, archives, and analyses posts ("Truths") from Donald Trump's Truth Social account. It helps ensure accountability by keeping a permanent, local record of all his posts—even if they are later deleted from the platform. The tool also tracks and displays his follower count, posting activity, and upvotes/shares of his posts/reuploads etc. making it easy to monitor trends in his popularity and engagement.

**Features:**
- Archives every post, including content, media, and engagement stats.
- Detects and saves new posts, even if old ones are deleted.
- Tracks follower and post counts over time.
- Provides search, stats, and trend analysis with easy-to-use menus.
- Visualizes posting frequency and follower growth.
- Easy to run with Python 3.x.
- A cartoon/pixel art of Trump is included for fun!
- If you do not want the cartoon Trump to show in the terminal. If you don't want the trump cartoon, comment out display_ascii_art() at the main_menu function:  
    <code>
    def main_menu():  
        #display_ascii_art()  
        smart_update()
    </code>


![Cartoon Trump](Trump.png)

