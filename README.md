# Telegram-SFT-Bot

I made a simple Telegram Bot to sign in and out for SFT on Google Sheets. Basically, a 'BIBO' book but digitised, which also sends a reminder to sign out at the end of SFT Timings.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install other libraries. Only required if you are going to run the bot locally.

```bash
pip install gspread
pip install oauth2client
pip install python-telegram-bot --upgrade
pip install pytz
```

## Usage

Rough things to be edited are shown below. For a detailed guide, please refer to the guides posted on the Telegram Channel. If you would like access to the channel, do send me a message.
```python
# Change SFT Timings
morning_start =  '07:00'
morning_end = '09:00'
night_start = '19:00'
night_end = '22:00'

# Change Subunits
[['BNHQ', 'ALPHA', 'BRAVO','MEC']]

# Most Importantly, remember to change the webhook
webhook_url= 'https://yourwebappname.herokuapp.com/'
```

## Contributing

Pull requests are welcome. Please create a pull request if you would like to improve any portion of the code, and I will update it accordingly. Thank you!


