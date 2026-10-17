/* Shared request-scoped translations. No network requests or application data mutation. */
(() => {
  'use strict';
  const element = document.getElementById('anmar-i18n');
  let context = {};
  try { context = JSON.parse(element?.textContent || '{}'); } catch { /* Portuguese fallback. */ }
  const locale = context.locale === 'es' ? 'es' : 'pt-BR';
  const messages = context.messages || {};
  const slot = /\{([A-Za-z_]\w*)\}/g;
  const own = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);
  const interpolate = (text, params) => text.replace(slot, (match, name) => own(params, name) ? String(params[name]) : match);
  const escapeRegex = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const patterns = Object.entries(messages).flatMap(([source, target]) => {
    const slots = [...source.matchAll(slot)];
    if (!slots.length) return [];
    const names = [];
    let pattern = '', offset = 0;
    for (const match of slots) {
      pattern += escapeRegex(source.slice(offset, match.index));
      const previous = names.indexOf(match[1]);
      pattern += previous < 0 ? '([\\s\\S]*?)' : `\\${previous + 1}`;
      if (previous < 0) names.push(match[1]);
      offset = match.index + match[0].length;
    }
    pattern += escapeRegex(source.slice(offset));
    return [{regex: new RegExp('^' + pattern + '$'), names, target}];
  });
  function t(message, params = {}) {
    message = message == null ? '' : String(message);
    if (locale !== 'es') return interpolate(message, params);
    if (own(messages, message)) return interpolate(messages[message], params);
    for (const {regex, names, target} of patterns) {
      const match = regex.exec(message);
      if (match) return interpolate(target, {...Object.fromEntries(names.map((name, i) => [name, match[i + 1]])), ...params});
    }
    return interpolate(message, params);
  }
  globalThis.AnmarI18n = Object.freeze({locale, t});
})();
