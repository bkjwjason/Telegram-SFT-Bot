# Telegram-SFT-Bot

</details>


> I made a simple Telegram Bot to sign in and out for SFT on Google Sheets. Also it sends a reminder to sign out at the end of SFT Timings. Basically, a 'BIBO' book but digitised, which also sends you reminders.

> This was made using Python and a few external libraries such as python-telegram-bot, sheets API (gspread).
>
> This bot is hosted on Heroku. I'm sure it can be improved further using a real external DB like Mongo, unfortunately Heroku does not offer the option for free tier. I'll have to make do with a dictionary instead. 

> Another problem I faced was users who did not sign out. Say if a user signed in on a Monday and forgot to sign out on the same Monday, it would be impossible for him to sign out on Tuesday. I tried using a JSON file to read/write data, so that a user can sign out on a different day as the sign in entry is still 'read' from the JSON file. However, Heroku does not allow modification and saving of files for more than 24 hours, so this approach is not feasible. Hence, I can only implement the reminder function for them to sign out, and if the user still does not sign out, the excel sheet sign out timing would be left empty.
> 
> Still working on some minor improvements, such as creating a new worksheet whenever it's a new month for simpler tracking purposes, and deleting older worksheets every few months as well. Looking into this mby using Google Apps Script, or maybe a cron-job executing a python file every month. Still rather unsure of the process.

> Apologies in advance for the spaghetti code 😬, do feel free to clone this repository and make your own edits and improvements to it. Thank you!

