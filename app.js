const cartCountEl = document.getElementById('cartCount');
const cartToast = document.getElementById('cartToast');
const addToCartButtons = document.querySelectorAll('.add-to-cart');
let cartCount = 0;

function showToast(message) {
  if (!cartToast) return;
  cartToast.textContent = message;
  cartToast.classList.add('cart-toast--visible');
  setTimeout(() => cartToast.classList.remove('cart-toast--visible'), 2200);
}

addToCartButtons.forEach((button) => {
  button.addEventListener('click', () => {
    cartCount += 1;
    if (cartCountEl) {
      cartCountEl.textContent = cartCount;
    }
    const productName = button.dataset.product || 'Букет';
    showToast(`«${productName}» добавлен в корзину`);
  });
});

const ctaForm = document.getElementById('ctaForm');
const formStatus = document.getElementById('formStatus');

function updateFormStatus(message, type) {
  if (!formStatus) return;
  formStatus.textContent = message;
  formStatus.classList.remove('form-status--success', 'form-status--error');
  if (type) {
    formStatus.classList.add(type === 'error' ? 'form-status--error' : 'form-status--success');
  }
}

if (ctaForm) {
  ctaForm.addEventListener('submit', (event) => {
    event.preventDefault();

    const name = ctaForm.elements.name?.value.trim() || '';
    const phone = ctaForm.elements.phone?.value.trim() || '';

    if (!name || !phone) {
      updateFormStatus('Пожалуйста, заполните имя и телефон.', 'error');
      return;
    }

    if (phone.replace(/\D/g, '').length < 10) {
      updateFormStatus('Укажите корректный номер телефона для связи.', 'error');
      return;
    }

    updateFormStatus('Отправляем заявку...', 'success');

    setTimeout(() => {
      updateFormStatus('Спасибо! Флорист свяжется с вами в течение 15 минут.', 'success');
      ctaForm.reset();
    }, 400);
  });
}

const faqToggles = document.querySelectorAll('.faq__toggle');

faqToggles.forEach((toggle) => {
  const panel = toggle.nextElementSibling;

  toggle.addEventListener('click', () => {
    const isOpen = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!isOpen));
    toggle.querySelector('.faq__icon').textContent = isOpen ? '+' : '–';
    if (panel) {
      panel.hidden = isOpen;
    }

    if (!isOpen) {
      toggle.focus();
    }
  });
});

// Фильтр подборок
const filterButtons = document.querySelectorAll('#collectionFilters .pill--button');
const bouquetCards = document.querySelectorAll('#bouquetGrid .product');

function applyFilter(filter) {
  bouquetCards.forEach((card) => {
    const tags = (card.dataset.tags || '').split(',');
    const matches = filter === 'all' || tags.includes(filter);
    card.classList.toggle('is-hidden', !matches);
  });
}

filterButtons.forEach((button) => {
  button.addEventListener('click', () => {
    filterButtons.forEach((btn) => btn.classList.remove('is-active'));
    button.classList.add('is-active');
    applyFilter(button.dataset.filter || 'all');
  });
});

applyFilter('all');

// Конструктор букета
const builderForm = document.getElementById('builderForm');
const builderOccasion = document.getElementById('builderOccasion');
const builderPalette = document.getElementById('builderPalette');
const builderPaletteButtons = document.querySelectorAll('[data-palette]');
const builderBudget = document.getElementById('builderBudget');
const builderSummary = document.getElementById('builderSummary');
const builderStatus = document.getElementById('builderStatus');
const sizeRadios = builderForm?.querySelectorAll('input[name="size"]') || [];
const etaForm = document.getElementById('etaForm');
const etaDistance = document.getElementById('etaDistance');
const etaMode = document.getElementById('etaMode');
const etaSummary = document.getElementById('etaSummary');
const etaStatus = document.getElementById('etaStatus');
const newsletterForm = document.getElementById('newsletterForm');
const newsletterStatus = document.getElementById('newsletterStatus');
const giftForm = document.getElementById('giftForm');
const giftAmount = document.getElementById('giftAmount');
const giftRecipient = document.getElementById('giftRecipient');
const giftNote = document.getElementById('giftNote');
const giftPreview = document.getElementById('giftPreview');
const giftStatus = document.getElementById('giftStatus');
const giftFormatRadios = document.querySelectorAll('input[name="giftFormat"]');

const occasionLabels = {
  birthday: 'для дня рождения',
  wedding: 'для свадьбы',
  home: 'для дома',
  office: 'для офиса',
  justbecause: 'без повода',
};

function formatCurrency(value) {
  return value.toLocaleString('ru-RU') + ' ₽';
}

function updateBuilderSummary() {
  if (!builderSummary) return;

  const occasion = builderOccasion?.value || 'justbecause';
  const palette = builderPalette?.value || 'tender';
  const paletteLabel =
    palette === 'contrast' ? 'контраст' : palette === 'mono' ? 'монохром' : 'нежные';

  let selectedSize = 'Миди';
  let sizeDelta = 0;
  sizeRadios.forEach((radio) => {
    if (radio.checked) {
      selectedSize = radio.nextElementSibling?.textContent || 'Миди';
      sizeDelta = Number(radio.dataset.delta || 0);
    }
  });

  const baseBudget = Number(builderBudget?.value || 0);
  const estimateMin = baseBudget + sizeDelta;
  const estimateMax = estimateMin + 800;

  builderSummary.querySelector('.builder__title').textContent = `Букет ${occasionLabels[occasion]}`;
  builderSummary.querySelector('.builder__meta').textContent = `Палитра: ${paletteLabel} • Размер: ${selectedSize}`;
  builderSummary.querySelector('.builder__budget').textContent = `Оценка бюджета: ${formatCurrency(
    estimateMin
  )} – ${formatCurrency(estimateMax)}`;
}

builderPaletteButtons.forEach((button) => {
  button.addEventListener('click', () => {
    builderPaletteButtons.forEach((btn) => btn.classList.remove('is-active'));
    button.classList.add('is-active');
    if (builderPalette) builderPalette.value = button.dataset.palette;
    updateBuilderSummary();
  });
});

builderOccasion?.addEventListener('change', updateBuilderSummary);
builderBudget?.addEventListener('input', updateBuilderSummary);
sizeRadios.forEach((radio) => radio.addEventListener('change', updateBuilderSummary));

builderForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  updateBuilderSummary();
  if (builderStatus) {
    builderStatus.textContent = 'Подбираем варианты…';
    builderStatus.classList.remove('form-status--error');
    builderStatus.classList.add('form-status--success');
  }
  setTimeout(() => {
    if (builderStatus) {
      builderStatus.textContent = 'Готово! Мы отправим 2–3 эскиза в течение 15 минут.';
    }
  }, 400);
});

updateBuilderSummary();

function updateEtaSummary() {
  if (!etaSummary) return;

  const distance = Number(etaDistance?.value || 0);
  const mode = etaMode?.value || 'standard';

  const baseTime = Math.max(45, distance * 9 + 30);
  const timeMultiplier = mode === 'express' ? 0.75 : mode === 'evening' ? 1.2 : 1;
  const etaMinutes = Math.round(baseTime * timeMultiplier);

  const baseCost = 250 + distance * 20;
  const costMultiplier = mode === 'express' ? 1.35 : mode === 'evening' ? 1.1 : 1;
  const cost = Math.round(baseCost * costMultiplier / 10) * 10;

  const modeLabel =
    mode === 'express'
      ? 'экспресс'
      : mode === 'evening'
      ? 'вечерняя после 18:00'
      : 'стандарт';

  etaSummary.querySelector('.eta__title').textContent = `Доставка за ${etaMinutes} минут`;
  etaSummary.querySelector('.eta__meta').textContent = `Оценка для ${distance} км, режим: ${modeLabel}`;
  etaSummary.querySelector('.eta__price').textContent = `Стоимость: ${formatCurrency(cost)}`;
}

etaDistance?.addEventListener('input', updateEtaSummary);
etaMode?.addEventListener('change', updateEtaSummary);

etaForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  updateEtaSummary();
  if (etaStatus) {
    etaStatus.textContent = 'Бронируем ближайший слот доставки…';
    etaStatus.classList.add('form-status--success');
  }
  setTimeout(() => {
    if (etaStatus) {
      etaStatus.textContent = 'Слот закреплён! Мы подтвердим время в течение 5 минут.';
    }
  }, 400);
});

updateEtaSummary();

newsletterForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!newsletterForm) return;

  const email = newsletterForm.elements.email?.value.trim();
  if (!email || !email.includes('@')) {
    if (newsletterStatus) {
      newsletterStatus.textContent = 'Укажите корректный e-mail, чтобы получать подборки.';
      newsletterStatus.classList.add('form-status--error');
      newsletterStatus.classList.remove('form-status--success');
    }
    return;
  }

  if (newsletterStatus) {
    newsletterStatus.textContent = 'Добавляем вас в рассылку…';
    newsletterStatus.classList.remove('form-status--error');
    newsletterStatus.classList.add('form-status--success');
  }

  setTimeout(() => {
    if (newsletterStatus) {
      newsletterStatus.textContent = 'Готово! Мы пришлём первое письмо уже на этой неделе.';
    }
    newsletterForm.reset();
  }, 400);
});

function selectedGiftFormatLabel() {
  let label = 'Цифровой';
  giftFormatRadios.forEach((radio) => {
    if (radio.checked) {
      label = radio.dataset.label || radio.value;
    }
  });
  return label;
}

function updateGiftPreview() {
  if (!giftPreview) return;

  const amount = Number(giftAmount?.value || 0);
  const recipient = giftRecipient?.value.trim() || 'Имя пока не указано';
  const note = giftNote?.value.trim();
  const formatLabel = selectedGiftFormatLabel();

  const amountEl = giftPreview.querySelector('.gift-preview__amount');
  if (amountEl) amountEl.textContent = formatCurrency(amount);

  const recipientEl = giftPreview.querySelector('.gift-preview__recipient');
  if (recipientEl) recipientEl.textContent = recipient;

  const badgeEl = giftPreview.querySelector('.badge');
  if (badgeEl) badgeEl.textContent = formatLabel;

  const noteEl = giftPreview.querySelector('.gift-preview__note');
  if (noteEl) {
    noteEl.textContent =
      note ||
      'Можем доставить завтра после 10:00 или отправить e-mail в указанную дату.';
  }
}

giftAmount?.addEventListener('input', updateGiftPreview);
giftRecipient?.addEventListener('input', updateGiftPreview);
giftNote?.addEventListener('input', updateGiftPreview);
giftFormatRadios.forEach((radio) => radio.addEventListener('change', updateGiftPreview));

giftForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  const amount = Number(giftAmount?.value || 0);
  const recipient = giftRecipient?.value.trim();

  if (!recipient) {
    if (giftStatus) {
      giftStatus.textContent = 'Укажите имя получателя, чтобы мы подписали открытку.';
      giftStatus.classList.add('form-status--error');
      giftStatus.classList.remove('form-status--success');
    }
    return;
  }

  if (amount < 1500) {
    if (giftStatus) {
      giftStatus.textContent = 'Минимальная сумма сертификата — 1 500 ₽.';
      giftStatus.classList.add('form-status--error');
      giftStatus.classList.remove('form-status--success');
    }
    return;
  }

  if (giftStatus) {
    giftStatus.textContent = 'Оформляем сертификат…';
    giftStatus.classList.remove('form-status--error');
    giftStatus.classList.add('form-status--success');
  }

  setTimeout(() => {
    if (giftStatus) {
      giftStatus.textContent = 'Готово! Мы отправим подтверждение и макет упаковки в течение 10 минут.';
    }
    giftForm.reset();
    updateGiftPreview();
  }, 450);
});

updateGiftPreview();
