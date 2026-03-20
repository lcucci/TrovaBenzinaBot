# TrovaBenzinaBot

[![it](https://img.shields.io/badge/lang-italiano-green.svg)](https://github.com/LorenzoQC/TrovaBenzinaBot/blob/main/README.it.md)

Telegram bot that allows users to find the cheapest fuel stations nearby in Italy.

## ✨ Features

* **Fuel stations search**: Finds stations offering the lowest prices for the selected fuel type near the user's
  location.
* **Geolocation**: Uses Telegram's location sharing to quickly locate nearby fuel stations.
* **Personalization**: Users can select their preferred language and fuel type.
* **Savings statistics**: Displays personalized statistics on the savings achieved by the user thanks to the bot.
* **Intuitive interface**: Simple commands and inline buttons for seamless navigation.

## 🛠️ Technologies used

* Python 3.12
* Telegram Bot API (`python-telegram-bot[webhooks]==22.2`)
* Web framework: `aiohttp==3.10.11` for webhook handling
* Database driver: `asyncpg>=0.27.0` for PostgreSQL
* ORM & async support: `SQLAlchemy[asyncio]>=2.0.0`
* File operations: `aiofiles~=24.1.0`


## 🚀 Deployment

The bot is currently deployed on [Railway](https://railway.app) and is available on Telegram
as [@trovabenzinabot](https://t.me/trovabenzinabot).

## 🗂️ Project structure

```plaintext
.
├── assets/                  # Static resources for the bot
│   ├── config/              # Additional configuration files
│   │   ├── csv/             # CSV data files
│   │   └── sql/             # Database initialization scripts
│   └── images/              # Images and icons
├── src/                     # Application source code
│   └── trovabenzina/
│       ├── api/             # External API integrations (Google Maps, MISE)
│       ├── config/          # Configuration and secret management
│       ├── core/            # Bot initialization and operational runners
│       ├── db/              # Database access and synchronization
│       ├── handlers/        # Command and conversation handlers
│       ├── i18n/            # Multilingual translation files
│       └── utils/           # Utility functions and helpers
├── requirements.txt         # Project dependencies
├── Dockerfile               # Docker configuration for deployment
└── README.md                # Project documentation
```

## 📌 Bot commands

* `/start`: Start user profile setup.
* `/search`: Search the cheapest fuel stations based on the current location.
* `/profile`: View or edit your profile preferences (language, fuel type).
* `/statistics`: View savings statistics.
* `/help`: Show help information and available commands.

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
