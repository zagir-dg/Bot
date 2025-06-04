from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_CHAT_ID  # ✅ Исправлено

router = Router()

class OrderStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_quantity = State()
    waiting_for_size = State()
    waiting_for_phone = State()

def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Оформить заказ", callback_data="order")],
        [InlineKeyboardButton(text="📏 Узнать размер", callback_data="size")],
        [InlineKeyboardButton(text="❓ Задать вопрос", callback_data="question")],
    ])
    return keyboard

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    name = message.from_user.first_name or "друг"
    await message.answer(
        f"Привет, {name}! 👋 Добро пожаловать в наш магазин одежды.\nВыбери, что хочешь сделать:",
        reply_markup=get_main_keyboard()
    )

@router.callback_query(F.data == "order")
async def handle_order(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Введите ваше имя:")
    await state.set_state(OrderStates.waiting_for_name)
    await callback.answer()

@router.callback_query(F.data == "size")
async def handle_size(callback: CallbackQuery):
    with open("sizes.png", "rb") as photo:
        await callback.message.answer_photo(photo=photo, caption="📏 Размерная сетка:")
    await callback.answer()

@router.callback_query(F.data == "question")
async def handle_question(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("❓ Напишите свой вопрос, и мы свяжемся с вами как можно скорее.")
    await state.set_state("waiting_for_question")
    await callback.answer()

@router.message(OrderStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите количество товара:")
    await state.set_state(OrderStates.waiting_for_quantity)

@router.message(OrderStates.waiting_for_quantity)
async def process_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите число.")
        return
    await state.update_data(quantity=int(message.text))
    await message.answer("Введите желаемый размер (например, S, M, L, XL):")
    await state.set_state(OrderStates.waiting_for_size)

@router.message(OrderStates.waiting_for_size)
async def process_size(message: Message, state: FSMContext):
    size = message.text.strip().upper()
    allowed_sizes = ["S", "M", "L", "XL"]
    if size not in allowed_sizes:
        await message.answer(f"Пожалуйста, выберите размер из списка: {', '.join(allowed_sizes)}")
        return
    await state.update_data(size=size)
    await message.answer("Введите номер для связи:")
    await state.set_state(OrderStates.waiting_for_phone)

@router.message(OrderStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    data = await state.get_data()
    name = data.get("name")
    quantity = data.get("quantity")
    size = data.get("size")

    order_text = (
        f"📦 Новый заказ:\n"
        f"Имя: {name}\n"
        f"Количество: {quantity}\n"
        f"Размер: {size}\n"
        f"Телефон: {phone}\n"
    )
    await message.bot.send_message(ADMIN_CHAT_ID, order_text)  # ✅ Исправлено
    await message.answer("✅ Спасибо! Ваш заказ принят. В ближайшее время с вами свяжемся для уточнения деталей и доставки.")
    await state.clear()

@router.message(F.state == "waiting_for_question")
async def process_question(message: Message, state: FSMContext):
    question_text = message.text
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    text = f"❓ Вопрос от {user_name} (id: {user_id}):\n{question_text}"
    await message.bot.send_message(ADMIN_CHAT_ID, text)  # ✅ Исправлено
    await message.answer("Спасибо за вопрос! Мы свяжемся с вами в ближайшее время.")
    await state.clear()
