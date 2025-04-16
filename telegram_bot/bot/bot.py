import telebot
import yaml
import os

config_file = os.getenv("BOT_CONFIG_FILE", "config.yaml")
with open(config_file, "r") as file:
    config = yaml.safe_load(file)

bot = telebot.TeleBot(config['telegram_token'])

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(chat_id=message.chat.id, text=f'👋 Привет! Я бот-оповещатель Oko-FreeVigilance. ID нашего чата: `{message.chat.id}`, его тебе нужно указывать при создании каналов оповещений', parse_mode='Markdown')

if __name__ == '__main__':
    bot.infinity_polling()
