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
