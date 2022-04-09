import collections
import json

from aiogram import Bot, types
from aiogram import executor
from aiogram.dispatcher import Dispatcher
from aiogram.types import BotCommand

from helpers import github_helper
from helpers import read_yaml
from helpers import state_machine

allowed = []
owners = [378542113, 853881966]
person_states = collections.defaultdict()
last_info = {}
last_message = collections.defaultdict()


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Начать работу с ботом"),
    ]
    await bot.set_my_commands(commands)


async def start_func(bot, message):
    key = types.InlineKeyboardMarkup()
    but_1 = types.InlineKeyboardButton(text='Добавить анализ',
                                       callback_data='add_text')
    but_2 = types.InlineKeyboardButton(text='Получить анализ',
                                       callback_data='get_text')
    but_5 = types.InlineKeyboardButton(text='Добавить пользователя',
                                       callback_data='add_user')
    key.add(but_1, but_2, but_5)
    text = 'Выберите, что хотите сделать:'
    await bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=key,
    )
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)


def main():
    bot = Bot(token=read_yaml.get_token_tg())
    dispatcher = Dispatcher(bot)
    all_data = github_helper.get_file_from_git('data.json')
    print(all_data)
    with open('data.json', 'wb') as file:
        file.write(all_data)
    with open('data.json', 'r') as f:
        all_data = json.load(f)

    @dispatcher.message_handler(commands=['start'])
    async def start(message):
        await set_commands(bot)
        if message['from'].username in allowed or \
                message.from_user.id in owners:
            await start_func(bot, message)

    @dispatcher.callback_query_handler(lambda call: True)
    async def callback_inline(call):
        if call.data == 'add_text':
            person_states[
                call.message.chat.id] = state_machine.ProjectStates.NAME
            res = await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text='Введите название анализируемого произведения:'
            )
            last_message[call.message.chat.id] = res
        elif call.data == 'back':
            await start_func(bot, call.message)
        elif call.data == 'get_text':
            person_states[
                call.message.chat.id] = state_machine.ProjectStates.GET_NAME
            res = await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text='Введите название анализируемого произведения:'
            )
            last_message[call.message.chat.id] = res
        elif call.data == 'add_user':
            person_states[
                call.message.chat.id] = state_machine.ProjectStates.ADD_USER
            res = await bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text='Введите username пользователя которого хотите добавить'
            )
            last_message[call.message.chat.id] = res

    @dispatcher.message_handler(content_types=['text'])
    async def text_mess(message):
        if person_states[
            message.from_user.id] == state_machine.ProjectStates.NAME or \
                person_states[
                    message.from_user.id] == state_machine.ProjectStates.GET_NAME:
            last_info['name'] = message.text
            if person_states[
                message.from_user.id] == state_machine.ProjectStates.NAME:
                person_states[
                    message.from_user.id] = state_machine.ProjectStates.AUTHOR
            elif person_states[
                message.from_user.id] == state_machine.ProjectStates.GET_NAME:
                person_states[
                    message.from_user.id] = state_machine.ProjectStates.GET_AUTHOR
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=last_message[message.from_user.id].message_id,
                text='Введите автора анализируемого произведения:'
            )
        elif person_states[
            message.from_user.id] == state_machine.ProjectStates.AUTHOR:
            last_info['author'] = message.text
            person_states[
                message.from_user.id] = state_machine.ProjectStates.TEXT
            res = await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=last_message[message.from_user.id].message_id,
                text='Введите сам текст анализа или пришлите документ:'
            )
            last_message[message.from_user.id] = res
        elif person_states[
            message.from_user.id] == state_machine.ProjectStates.GET_AUTHOR:
            last_info['author'] = message.text
            key = types.InlineKeyboardMarkup()
            but_1 = types.InlineKeyboardButton(text='Назад',
                                               callback_data='back')
            key.add(but_1)
            try:
                smth = all_data[last_info['name'] + '_' + last_info['author']]
            except:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=last_message[message.from_user.id].message_id,
                    text=f"Сохраненного анализа для произведения *{last_info['name']}* под авторством *{last_info['author']}* нет",
                    reply_markup=key,
                    parse_mode="Markdown",
                )
            try:
                await bot.send_document(message.from_user.id, all_data[
                    last_info['name'] + '_' + last_info['author']])
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=last_message[message.from_user.id].message_id,
                    text='Выберите что делать дальше',
                    reply_markup=key,
                )
            except:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=last_message[message.from_user.id].message_id,
                    text=all_data[last_info['name'] + '_' + last_info['author']],
                    reply_markup=key,
                )
        elif person_states[
            message.from_user.id] == state_machine.ProjectStates.TEXT:
            last_info['text'] = message.text
            person_states[
                message.from_user.id] = None
            key = types.InlineKeyboardMarkup()
            but_1 = types.InlineKeyboardButton(text='Назад',
                                               callback_data='back')
            key.add(but_1)
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=last_message[message.from_user.id].message_id,
                text='Успешно сохранил информацию',
                reply_markup=key,
            )
            all_data[last_info['name'] + '_' + last_info['author']] = last_info[
                'text']
            with open(last_info['name'] + '.docx', 'w') as file:
                file.write(message.text)
            github_helper.upload_file_to_git(last_info['name'] + '.docx',
                                             message.text)
            read_yaml.save_data(last_info)
        await bot.delete_message(chat_id=message.chat.id,
                                 message_id=message.message_id)

    @dispatcher.message_handler(content_types=['document'])
    async def content_mess(message):
        if person_states[
            message.from_user.id] == state_machine.ProjectStates.TEXT:
            last_info['text'] = message.document.file_id
            person_states[
                message.from_user.id] = None
            key = types.InlineKeyboardMarkup()
            but_1 = types.InlineKeyboardButton(text='Назад',
                                               callback_data='back')
            key.add(but_1)
            await bot.send_message(
                chat_id=message.chat.id,
                text='Успешно сохранил информацию',
                reply_markup=key,
            )
            try:
                await bot.delete_message(
                    message_id=last_message[message.from_user.id],
                    chat_id=message.chat.id,
                )
            except Exception as exc:
                print(exc)
            all_data[last_info['name'] + '_' + last_info['author']] = last_info[
                'text']
            await bot.delete_message(chat_id=message.chat.id,
                                     message_id=message.message_id)
            read_yaml.save_data(last_info)

    executor.start_polling(dispatcher, skip_updates=True)


if __name__ == '__main__':
    main()
