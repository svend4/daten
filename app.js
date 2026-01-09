const form = document.querySelector('.cta__form');
const statusLine = document.querySelector('.cta__status');

const setStatus = (message, tone) => {
  if (!statusLine) return;
  statusLine.textContent = message;
  statusLine.classList.remove('cta__status--error', 'cta__status--success', 'cta__status--pending');
  if (tone) {
    statusLine.classList.add(`cta__status--${tone}`);
  }
};

const isPhoneValid = (phone) => {
  const cleaned = phone.replace(/[^\d+]/g, '');
  return cleaned.length >= 7 && /^\+?\d{7,15}$/.test(cleaned);
};

if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    const nameInput = form.querySelector('input[aria-label="Имя"]');
    const phoneInput = form.querySelector('input[aria-label="Телефон"]');
    const name = nameInput?.value.trim() || '';
    const phone = phoneInput?.value.trim() || '';

    if (!name) {
      setStatus('Введите имя, чтобы мы знали, как к вам обратиться.', 'error');
      nameInput?.focus();
      return;
    }

    if (!isPhoneValid(phone)) {
      setStatus('Укажите корректный номер телефона в международном формате.', 'error');
      phoneInput?.focus();
      return;
    }

    setStatus('Отправляем заявку...', 'pending');

    try {
      await new Promise((resolve) => setTimeout(resolve, 600));
      form.reset();
      setStatus('Спасибо! Мы свяжемся с вами в течение 15 минут.', 'success');
    } catch (error) {
      setStatus('Не удалось отправить заявку. Попробуйте снова позже.', 'error');
      console.error('Ошибка отправки формы', error);
    }
  });
}
