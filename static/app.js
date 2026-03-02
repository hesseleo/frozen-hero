// ── i18n ───────────────────────────────────────────────────────────
const TRANSLATIONS = {
   de: {
      tab_new_label:  "Neues Label",
      tab_show_list:  "Liste",
      label_row1:     "Erste Zeile",
      label_row2:     "Zweite Zeile",
      label_category: "Kategorie",
      label_amount:   "Menge",
      label_date:     "Haltbar bis",
      btn_print:      "DRUCKEN",
      modal_printing: "Wird gedruckt… :)",
      cat_placeholder: "Bitte wählen …",
      cat_selfstuff:  "Selbstgekochtes",
      cat_vegetable:  "Gemüse",
      cat_herbs:      "Kräuter",
      cat_meat:       "Fleisch",
      cat_sausage:    "Wurst",
      cat_pastries:   "Backwaren",
      cat_diary:      "Milchprodukte",
      cat_fruits:     "Obst",
      cat_butter:     "Butter",
      cat_cake:       "Kuchen",
      cat_fish:       "Fisch",
      delete_title:    "Eintrag löschen",
      delete:          "Löschen",
      cancel:          "Abbrechen",
      list_empty:      "Keine Einträge",
      tip_row1:        "Pflichtfeld. Wird als große Titelzeile auf dem Etikett gedruckt. Maximal 20 Zeichen.",
      tip_row2:        "Optional. Wird als kleinere Zusatzzeile auf dem Etikett gedruckt. Maximal 64 Zeichen.",
      tip_category:    "Optional. Setzt das Haltbarkeitsdatum automatisch anhand typischer Lagerzeiten. Das Datum kann danach manuell angepasst werden.",
      tip_amount:      "Pflichtfeld. Anzahl der zu druckenden Etiketten in einem Durchgang.",
      tip_date:        "Pflichtfeld. Das Datum wird auf das Etikett gedruckt und in der Übersicht angezeigt. Wird automatisch gesetzt, wenn eine Kategorie gewählt wird.",
   },
   en: {
      tab_new_label:  "New Label",
      tab_show_list:  "List",
      label_row1:     "First line",
      label_row2:     "Second line",
      label_category: "Category",
      label_amount:   "Quantity",
      label_date:     "Best before",
      btn_print:      "PRINT",
      modal_printing: "Printing… :)",
      cat_placeholder: "Please select …",
      cat_selfstuff:  "Home-cooked",
      cat_vegetable:  "Vegetables",
      cat_herbs:      "Herbs",
      cat_meat:       "Meat",
      cat_sausage:    "Sausage",
      cat_pastries:   "Bakery",
      cat_diary:      "Dairy",
      cat_fruits:     "Fruit",
      cat_butter:     "Butter",
      cat_cake:       "Cake",
      cat_fish:       "Fish",
      tip_row1:        "Required. Printed as the large title on the label. Maximum 20 characters.",
      tip_row2:        "Optional. Printed as a smaller subtitle on the label. Maximum 64 characters.",
      tip_category:    "Optional. Automatically sets the best-before date based on typical shelf life per category. The date can be adjusted manually afterwards.",
      tip_amount:      "Required. How many labels to print in one go.",
      tip_date:        "Required. Printed on the label and shown in the inventory. Automatically set when a category is selected.",
      delete_title:    "Delete entry",
      delete:          "Delete",
      cancel:          "Cancel",
      list_empty:      "No entries",
   },
};

let currentLang = localStorage.getItem('lang') || 'de';

function t(key, vars = {}) {
   let str = (TRANSLATIONS[currentLang] || TRANSLATIONS.de)[key] || key;
   for (const [k, v] of Object.entries(vars)) str = str.replaceAll(`{${k}}`, v);
   return str;
}

function setLanguage(lang) {
   currentLang = lang;
   localStorage.setItem('lang', lang);
   document.querySelectorAll('[data-i18n]').forEach(el => {
      el.textContent = t(el.dataset.i18n);
   });
   document.querySelectorAll('[data-i18n-static]').forEach(el => {
      el.textContent = t(el.dataset.i18nStatic);
   });
   document.querySelectorAll('[data-iso-date]').forEach(el => {
      el.textContent = formatDisplayDate(el.dataset.isoDate);
   });
   document.getElementById('lang-select').value = lang;
}

// ── View switching ─────────────────────────────────────────────────
function showView(name) {
   document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
   document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
   document.getElementById('view-' + name).classList.add('active');
   document.getElementById('nav-' + name).classList.add('active');
   if (name === 'list') updateList();
}

// ── Swipe library (minified) ───────────────────────────────────────
!function(t,e){"use strict";"function"!=typeof t.CustomEvent&&(t.CustomEvent=function(t,n){n=n||{bubbles:!1,cancelable:!1,detail:void 0};var a=e.createEvent("CustomEvent");return a.initCustomEvent(t,n.bubbles,n.cancelable,n.detail),a},t.CustomEvent.prototype=t.Event.prototype),e.addEventListener("touchstart",function(t){if("true"===t.target.getAttribute("data-swipe-ignore"))return;s=t.target,r=Date.now(),n=t.touches[0].clientX,a=t.touches[0].clientY,u=0,i=0},!1),e.addEventListener("touchmove",function(t){if(!n||!a)return;var e=t.touches[0].clientX,r=t.touches[0].clientY;u=n-e,i=a-r},!1),e.addEventListener("touchend",function(t){if(s!==t.target)return;var e=parseInt(l(s,"data-swipe-threshold","20"),10),o=parseInt(l(s,"data-swipe-timeout","500"),10),c=Date.now()-r,d="",p=t.changedTouches||t.touches||[];Math.abs(u)>Math.abs(i)?Math.abs(u)>e&&c<o&&(d=u>0?"swiped-left":"swiped-right"):Math.abs(i)>e&&c<o&&(d=i>0?"swiped-up":"swiped-down");if(""!==d){var b={dir:d.replace(/swiped-/,""),touchType:(p[0]||{}).touchType||"direct",xStart:parseInt(n,10),xEnd:parseInt((p[0]||{}).clientX||-1,10),yStart:parseInt(a,10),yEnd:parseInt((p[0]||{}).clientY||-1,10)};s.dispatchEvent(new CustomEvent("swiped",{bubbles:!0,cancelable:!0,detail:b})),s.dispatchEvent(new CustomEvent(d,{bubbles:!0,cancelable:!0,detail:b}))}n=null,a=null,r=null},!1);var n=null,a=null,u=null,i=null,r=null,s=null;function l(t,n,a){for(;t&&t!==e.documentElement;){var u=t.getAttribute(n);if(u)return u;t=t.parentNode}return a}}(window,document);

// ── Utilities ──────────────────────────────────────────────────────
function getDateFormat(date = new Date()) {
   const d = String(date.getDate()).padStart(2, '0');
   const m = String(date.getMonth() + 1).padStart(2, '0');
   return `${date.getFullYear()}-${m}-${d}`;
}

function formatDisplayDate(iso) {
   const [y, m, d] = iso.split('-');
   const date = new Date(+y, +m - 1, +d);
   const locale = currentLang === 'de' ? 'de-DE' : 'en-GB';
   return new Intl.DateTimeFormat(locale, { day: '2-digit', month: '2-digit', year: 'numeric' }).format(date);
}

// ── Data ───────────────────────────────────────────────────────────
function fetchEntries(cb) {
   const xhr = new XMLHttpRequest();
   xhr.open('GET', '/getData');
   xhr.setRequestHeader('Content-Type', 'application/json');
   xhr.onreadystatechange = function() {
      if (this.readyState === 4) cb(JSON.parse(this.responseText));
   };
   xhr.send(null);
}

function updateList() { fetchEntries(renderList); }

function renderList(list) {
   const container = document.getElementById('list-container');
   container.innerHTML = '';

   if (list.length === 0) {
      const el = document.createElement('div');
      el.className = 'list-empty';
      el.textContent = t('list_empty');
      container.appendChild(el);
      return;
   }

   const today = getDateFormat();
   list.forEach(entry => {
      const expired = entry.date < today;
      const item    = document.createElement('div');
      item.className = 'list-item' + (expired ? ' expired' : '');
      item.dataset.id     = entry.id;
      item.dataset.rowOne = entry.row_one;
      item.dataset.rowTwo = entry.row_two || '';

      const info = document.createElement('div');
      info.className = 'item-info';

      const nameEl = document.createElement('div');
      nameEl.className = 'item-name';
      nameEl.textContent = entry.row_one;
      info.appendChild(nameEl);

      if (entry.row_two) {
         const tagEl = document.createElement('div');
         tagEl.className = 'item-tag';
         tagEl.textContent = entry.row_two;
         info.appendChild(tagEl);
      }

      const dateEl = document.createElement('div');
      dateEl.className = 'item-date';
      dateEl.dataset.isoDate = entry.date;
      dateEl.textContent = formatDisplayDate(entry.date);

      const delBtn = document.createElement('button');
      delBtn.className = 'btn-delete';
      delBtn.setAttribute('data-swipe-ignore', 'true');
      delBtn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>';
      delBtn.addEventListener('click', () => deleteEntry(item));

      item.appendChild(info);
      item.appendChild(dateEl);
      item.appendChild(delBtn);

      item.addEventListener('swiped-left',  () => deleteEntry(item));
      item.addEventListener('swiped-right', () => deleteEntry(item));

      container.appendChild(item);
   });
}

function openSheet(item) {
   document.getElementById('sheet-title').textContent = t('delete_title');
   const sub = document.getElementById('sheet-subtitle');
   sub.innerHTML = '';
   const nameNode = document.createTextNode(item.dataset.rowOne);
   sub.appendChild(nameNode);
   if (item.dataset.rowTwo) {
      const tag = document.createElement('div');
      tag.className = 'sheet-tag';
      tag.textContent = item.dataset.rowTwo;
      sub.appendChild(tag);
   }
   document.getElementById('sheet-confirm').onclick = () => {
      closeSheet();
      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/delEntry');
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.onreadystatechange = function() {
         if (xhr.readyState === 4 && xhr.status === 200) updateList();
      };
      xhr.send(JSON.stringify({ id: parseInt(item.dataset.id) }));
   };
   document.getElementById('sheet-overlay').classList.add('open');
   document.getElementById('delete-sheet').classList.add('open');
}

function closeSheet() {
   document.getElementById('sheet-overlay').classList.remove('open');
   document.getElementById('delete-sheet').classList.remove('open');
}

function deleteEntry(item) { openSheet(item); }

// ── Category → shelf life ──────────────────────────────────────────
const KEEPABILITY = {
   selfstuff: 2, vegetable: 9, herbs: 8, meat: 5, sausage: 2,
   pastries: 2, diary: 3, fruits: 10, butter: 7, cake: 4, fish: 2,
};
let choosenCategory = '';

document.getElementById('my-select').addEventListener('change', function() {
   choosenCategory = this.value;
   const d = new Date(getDateFormat());
   d.setMonth(d.getMonth() + (KEEPABILITY[this.value] || 0));
   document.getElementById('date').value = getDateFormat(d);
});

// ── Print ──────────────────────────────────────────────────────────
function showToast(msg) {
   const el = document.getElementById('toast');
   el.textContent = msg;
   el.classList.add('show');
}

function hideToast() {
   document.getElementById('toast').classList.remove('show');
}

function printButtonClick() {
   const row1   = document.getElementById('row1').value.trim();
   const row2   = document.getElementById('row2').value.trim();
   const date   = document.getElementById('date').value;
   const amount = document.getElementById('select_amount').selectedIndex + 1;

   if (!row1 || !date) return;

   const data = { row1, row2, category: choosenCategory, date };
   let sent = 0;

   showToast(t('modal_printing'));

   function sendOne() {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', '/add2freezer');
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.onreadystatechange = function() {
         if (xhr.readyState !== 4 || xhr.status !== 201) return;
         sent++;
         if (sent < amount) { sendOne(); return; }
         hideToast();
         document.getElementById('row1').value = '';
         document.getElementById('row2').value = '';
         document.getElementById('date').value = getDateFormat();
         document.getElementById('my-select').value = '';
         document.getElementById('select_amount').selectedIndex = 0;
         choosenCategory = '';
      };
      xhr.send(JSON.stringify(data));
   }
   sendOne();
}

// ── Info tips ──────────────────────────────────────────────────────
function toggleTip(btn) {
   const tip = btn.closest('.field-header').nextElementSibling;
   const isOpen = tip.classList.contains('open');
   document.querySelectorAll('.info-tip.open').forEach(t => t.classList.remove('open'));
   if (!isOpen) tip.classList.add('open');
}

document.addEventListener('click', function(e) {
   if (!e.target.closest('.info-btn')) {
      document.querySelectorAll('.info-tip.open').forEach(t => t.classList.remove('open'));
   }
});

// ── Init ───────────────────────────────────────────────────────────
document.getElementById('date').value = getDateFormat();
setLanguage(currentLang);
fetchEntries(renderList);
