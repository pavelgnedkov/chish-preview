/* Отправка форм сайта chish.ru без WordPress: собирает поля с подписями и шлёт на /send.php */
(function () {
  function label(el) {
    var id = el.id && document.querySelector('label[for="' + el.id + '"]');
    if (id) return id.textContent.trim();
    var p = el.closest('label, p, .contacts-form__item, div');
    var t = p ? (p.textContent || '').replace(el.value || '', '').trim().split('\n')[0].trim() : '';
    return t || el.placeholder || el.name;
  }
  function msg(form, text, ok) {
    var box = form.querySelector('.wpcf7-response-output');
    if (!box) { box = document.createElement('div'); form.appendChild(box); }
    box.className = 'wpcf7-response-output';
    box.style.cssText = 'display:block;margin-top:12px;padding:10px;border:2px solid ' + (ok ? '#46b450' : '#dc3232') + ';color:inherit';
    box.textContent = text;
  }
  document.querySelectorAll('form.wpcf7-form [type=submit][disabled]').forEach(function (b) { b.removeAttribute('disabled'); });
  window.addEventListener('submit', function (e) {
    var form = e.target;
    if (!form.classList || !form.classList.contains('wpcf7-form')) return;
    e.preventDefault(); e.stopImmediatePropagation(); e.stopPropagation();
    var acc = form.querySelector('input[type=checkbox][name^="acceptance"]');
    if (acc && !acc.checked) { msg(form, 'Отметьте согласие с Политикой конфиденциальности.', false); return; }
    var lines = [], filled = 0;
    form.querySelectorAll('input, textarea, select').forEach(function (el) {
      if (!el.name || el.name.charAt(0) === '_' || /recaptcha|acceptance/.test(el.name)) return;
      if (['submit', 'hidden', 'checkbox', 'radio', 'button'].indexOf(el.type) >= 0) return;
      var v = (el.value || '').trim();
      if (el.required || /validates-as-required/.test(el.className)) { if (!v) { filled = -1e9; } }
      if (v) { lines.push(label(el) + ': ' + v); filled++; }
    });
    if (filled <= 0) { msg(form, 'Заполните обязательные поля.', false); return; }
    var btn = form.querySelector('[type=submit]'); if (btn) btn.disabled = true;
    var fd = new FormData();
    fd.append('page', location.pathname); fd.append('text', lines.join('\n')); fd.append('website', '');
    fetch('/send.php', { method: 'POST', body: fd }).then(function (r) { return r.json(); }).then(function (j) {
      msg(form, j.ok ? 'Спасибо! Сообщение отправлено, мы свяжемся с вами.' : (j.error || 'Не удалось отправить. Позвоните нам: 8 (8442) 711-738'), j.ok);
      if (j.ok) form.reset();
    }).catch(function () {
      msg(form, 'Не удалось отправить. Позвоните нам: 8 (8442) 711-738 или напишите на chish.school@gmail.com', false);
    }).finally(function () { if (btn) btn.disabled = false; });
  }, true);
})();
