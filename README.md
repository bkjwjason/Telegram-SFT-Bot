# Telegram-SFT-Bot

</details>


> I made a simple Telegram Bot to sign in and out for SFT on Google Sheets. Also it sends a reminder to sign out at the end of SFT Timings. Basically, a 'BIBO' book but digitised, which also sends you reminders.

> This was made using Python and a few external libraries such as python-telegram-bot, sheets API (gspread).
>
> This bot is hosted on Heroku. I'm sure it can be improved further using a real external DB like Mongo, unfortunately Heroku does not offer the option for free tier. Hence, I just made do with a dictionary instead.

> Another problem I faced was users who did not sign out. Say if a user signed in on a Monday and forgot to sign out on the same Monday, it would be impossible for him to sign out on Tuesday as Heroku will reset the dyno (cloud) every 24 hours. I tried using a JSON file to read/write data, so that a user can sign out on a different day as the sign in entry is still 'read' from the JSON file. However, Heroku does not allow modification and saving of files for more than 24 hours, so this approach is not feasible. This approach may be possible if hosted on a different platform. Hence, I could only implement the reminder functionality for users to sign out.
> 
> Still working on some minor improvements, such as creating a new worksheet whenever it's a new month for simpler tracking purposes, and deleting older worksheets every few months as well. Looking into this by using Google Apps Script, or maybe a cron-job executing a python file every month. Still rather unsure of the process.

> Apologies in advance for the spaghetti code 😬, do feel free to clone/fork this repository and make your own edits and improvements to it. Do create a pull request if you can make further improvements. Thank you!

