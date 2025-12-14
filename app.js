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
