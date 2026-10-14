/* Datas brasileiras na tela; campos originais preservam o contrato ISO dos apps. */
(() => {
  'use strict';
  const states = new WeakMap();
  let sequence = 0;
  const descriptors = Object.fromEntries(['value', 'valueAsDate', 'valueAsNumber'].map(
    key => [key, Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, key)]
  ));
  const format = (value) => value ? value.split('-').reverse().join('/') : '';
  function parse(text, month) {
    const match = text.match(month ? /^(\d{2})\/(\d{4})$/ : /^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (!match) return '';
    const [day, mon, year] = month ? [1, +match[1], +match[2]] : [+match[1], +match[2], +match[3]];
    const date = new Date(0);
    date.setUTCFullYear(year, mon - 1, day);
    if (year < 1 || date.getUTCFullYear() !== year || date.getUTCMonth() !== mon - 1 || date.getUTCDate() !== day) return '';
    return `${String(year).padStart(4, '0')}-${String(mon).padStart(2, '0')}${month ? '' : '-' + String(day).padStart(2, '0')}`;
  }
  function enhance(native) {
    if (states.has(native) || native.hasAttribute('data-native-date')) return;
    const month = native.getAttribute('type') === 'month';
    const wrapper = document.createElement('span');
    wrapper.className = 'anmar-date-control';
    const display = document.createElement('input');
    display.type = 'text';
    display.inputMode = 'numeric';
    display.autocomplete = 'off';
    display.placeholder = month ? 'MM/AAAA' : 'DD/MM/AAAA';
    display.className = native.className;
    display.classList.add('anmar-date-display');
    if (!native.id) native.id = 'anmar-date-' + (++sequence);
    display.id = native.id + '--br';
    display.dataset.dateFor = native.id;
    const labels = [...native.labels];
    const label = native.getAttribute('aria-label') || labels.map(l => l.textContent.trim()).join(' ') || (month ? 'Mês' : 'Data');
    display.setAttribute('aria-label', label);
    for (const attr of ['aria-describedby', 'aria-labelledby', 'form', 'title']) {
      if (native.hasAttribute(attr)) display.setAttribute(attr, native.getAttribute(attr));
    }
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'anmar-date-picker';
    button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 11h18M8 15h2M14 15h2M8 18h2"/></svg>';
    button.setAttribute('aria-label', 'Abrir calendário: ' + label);
    button.title = 'Abrir calendário';
    button.hidden = native.type === 'text';
    const sync = () => {
      display.value = format(native.value);
      display.required = native.required;
      display.disabled = native.disabled;
      display.readOnly = native.readOnly;
      button.disabled = native.disabled || native.readOnly;
      wrapper.hidden = native.hidden;
      validate();
    };
    function validate() {
      let message = '';
      if (display.value && !parse(display.value, month)) message = 'Informe uma data válida no formato ' + display.placeholder + '.';
      else if (native.value && native.min && native.value < native.min) message = 'Use uma data a partir de ' + format(native.min) + '.';
      else if (native.value && native.max && native.value > native.max) message = 'Use uma data até ' + format(native.max) + '.';
      else if (native.validity.stepMismatch) message = 'Escolha uma data permitida no calendário.';
      else if (native.validity.customError) message = native.validationMessage;
      else if (native.required && !display.value) message = 'Informe ' + (month ? 'o mês.' : 'a data.');
      display.setCustomValidity(message);
    }
    states.set(native, {sync});
    native.before(wrapper);
    wrapper.append(native, display, button);
    native.classList.add('anmar-date-native');
    native.tabIndex = -1;
    native.setAttribute('aria-hidden', 'true');
    labels.forEach(l => { if (l.htmlFor === native.id) l.htmlFor = display.id; });
    // Inicializações e edições feitas pelos scripts existentes também atualizam a tela.
    for (const [key, descriptor] of Object.entries(descriptors)) {
      Object.defineProperty(native, key, {
        configurable: true,
        get() { return descriptor.get.call(this); },
        set(value) { descriptor.set.call(this, value); sync(); }
      });
    }
    function update(eventType) {
      descriptors.value.set.call(native, parse(display.value, month));
      validate();
      native.dispatchEvent(new Event(eventType, {bubbles: true}));
    }
    display.addEventListener('input', () => {
      const caretDigits = display.value.slice(0, display.selectionStart).replace(/\D/g, '').length;
      const digits = display.value.replace(/\D/g, '').slice(0, month ? 6 : 8);
      display.value = digits.slice(0, 2) + (digits.length > 2 ? '/' + digits.slice(2, month ? 6 : 4) : '') + (!month && digits.length > 4 ? '/' + digits.slice(4) : '');
      let caret = 0, seen = 0;
      while (caret < display.value.length && seen < caretDigits) { if (/\d/.test(display.value[caret])) seen++; caret++; }
      display.setSelectionRange(caret, caret);
      update('input');
    });
    display.addEventListener('paste', event => {
      if (!event.clipboardData) return;
      event.preventDefault();
      const text = event.clipboardData.getData('text/plain').trim();
      const parts = text.split('/');
      display.value = parts.length === (month ? 2 : 3)
        ? parts.map((part, index) => index < parts.length - 1 ? part.padStart(2, '0') : part).join('/')
        : /^\d+$/.test(text) && text.length === (month ? 6 : 8)
          ? text.slice(0, 2) + '/' + text.slice(2, month ? 6 : 4) + (month ? '' : '/' + text.slice(4))
          : text;
      update('input');
    });
    display.addEventListener('change', () => { if (!display.value || parse(display.value, month)) update('change'); });
    // Calendário nativo e atribuições externas continuam emitindo os eventos do campo original.
    native.addEventListener('input', event => { if (event.isTrusted) sync(); });
    native.addEventListener('change', event => { if (event.isTrusted) sync(); });
    native.addEventListener('focus', () => display.focus());
    native.addEventListener('invalid', event => {
      event.preventDefault();
      validate();
      display.focus();
      display.reportValidity();
    });
    button.addEventListener('click', () => {
      if (native.showPicker) native.showPicker();
      else { native.focus(); native.click(); }
    });
    native.form?.addEventListener('reset', () => setTimeout(sync, 0));
    new MutationObserver(sync).observe(native, {attributes: true, attributeFilter: ['value', 'required', 'disabled', 'readonly', 'min', 'max', 'step', 'hidden']});
    sync();
  }
  function scan(root) {
    if (root.matches?.('input[type="date"], input[type="month"]')) enhance(root);
    root.querySelectorAll?.('input[type="date"], input[type="month"]').forEach(enhance);
  }
  function start() {
    scan(document);
    new MutationObserver(records => records.forEach(r => r.addedNodes.forEach(scan))).observe(document.body, {childList: true, subtree: true});
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
