// Main JavaScript for Manufactor Flask UI

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');

    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Card sort and group controls
    const sortSelect = document.getElementById('sort-select');
    const groupSelect = document.getElementById('group-select');
    if (sortSelect && groupSelect) {
        sortSelect.addEventListener('change', applyCardControls);
        groupSelect.addEventListener('change', applyCardControls);
        // Apply defaults immediately on page load
        applyCardControls();
    }
});

// --- Card Sort & Group ---

// Snapshot of the original card elements, captured once on first call.
// Using a canonical list prevents tag-grouping clones from being double-counted
// on subsequent group-by changes.
let _canonicalCardItems = null;

function getCanonicalItems() {
    if (!_canonicalCardItems) {
        _canonicalCardItems = Array.from(document.querySelectorAll('.card-gallery-item'));
    }
    return _canonicalCardItems;
}

function getManaValue(cost) {
    if (!cost) return 0;
    let cmc = 0;
    const matches = cost.match(/\{([^}]+)\}/g) || [];
    for (const sym of matches) {
        const inner = sym.slice(1, -1).toUpperCase();
        const num = parseInt(inner, 10);
        if (!isNaN(num)) {
            cmc += num;
        } else if (inner === 'X' || inner === 'Y' || inner === 'Z') {
            // variable mana counts as 0
        } else {
            // colour pip, hybrid, phyrexian, snow — each counts as 1
            cmc += 1;
        }
    }
    return cmc;
}

const TYPE_ORDER = ['Creature', 'Planeswalker', 'Instant', 'Sorcery', 'Enchantment', 'Artifact', 'Land', 'Battle', 'Other'];

function normalizeCardType(cardtype) {
    if (!cardtype) return 'Other';
    const ct = cardtype.toLowerCase();
    for (const t of TYPE_ORDER) {
        if (ct.includes(t.toLowerCase())) return t;
    }
    return 'Other';
}

function applyCardControls() {
    const sortSelect = document.getElementById('sort-select');
    const groupSelect = document.getElementById('group-select');
    const cardList = document.querySelector('.card-list');
    if (!sortSelect || !groupSelect || !cardList) return;

    const sortBy = sortSelect.value;
    const groupBy = groupSelect.value;

    // Always work from the canonical snapshot, not whatever is currently in the DOM
    // (tag grouping leaves clones in the DOM that would inflate counts otherwise)
    const allItems = [...getCanonicalItems()];
    if (!allItems.length) return;

    // Sort
    allItems.sort(function(a, b) {
        if (sortBy === 'mana') {
            const mvA = getManaValue(a.dataset.cost);
            const mvB = getManaValue(b.dataset.cost);
            // CMC 0 (lands, X-spells, etc.) sorts to the very end
            const sortA = mvA === 0 ? Number.MAX_SAFE_INTEGER : mvA;
            const sortB = mvB === 0 ? Number.MAX_SAFE_INTEGER : mvB;
            if (sortA !== sortB) return sortA - sortB;
        }
        return (a.dataset.name || '').localeCompare(b.dataset.name || '');
    });

    // Tear down existing galleries / groups
    cardList.querySelectorAll('.card-gallery, .card-group').forEach(function(el) { el.remove(); });

    if (groupBy === 'none') {
        const gallery = document.createElement('div');
        gallery.className = 'card-gallery';
        allItems.forEach(function(item) { gallery.appendChild(item); });
        cardList.appendChild(gallery);
        return;
    }

    // Build group map
    const groupMap = new Map();

    allItems.forEach(function(item) {
        let keys;
        if (groupBy === 'type') {
            keys = [normalizeCardType(item.dataset.cardtype)];
        } else if (groupBy === 'landnonland') {
            const ct = (item.dataset.cardtype || '').toLowerCase();
            keys = [ct.includes('land') ? 'Land' : 'Nonland'];
        } else {
            // tag
            const tagStr = (item.dataset.tags || '').trim();
            const tags = tagStr ? tagStr.split(',').map(function(t) { return t.trim(); }).filter(Boolean) : [];
            keys = tags.length > 0 ? tags : ['Untagged'];
        }

        keys.forEach(function(key, i) {
            if (!groupMap.has(key)) groupMap.set(key, []);
            // Clone the element when a card belongs to multiple tag groups
            const el = (i < keys.length - 1) ? item.cloneNode(true) : item;
            groupMap.get(key).push(el);
        });
    });

    // Sort group keys
    let groupKeys = Array.from(groupMap.keys());
    if (groupBy === 'type') {
        groupKeys.sort(function(a, b) {
            const ia = TYPE_ORDER.indexOf(a);
            const ib = TYPE_ORDER.indexOf(b);
            return (ia < 0 ? 999 : ia) - (ib < 0 ? 999 : ib);
        });
    } else if (groupBy === 'landnonland') {
        // Nonland first, Land second
        groupKeys.sort(function(a) { return a === 'Nonland' ? -1 : 1; });
    } else {
        groupKeys.sort(function(a, b) {
            if (a === 'Untagged') return 1;
            if (b === 'Untagged') return -1;
            return a.localeCompare(b);
        });
    }

    // Render groups
    groupKeys.forEach(function(key) {
        const items = groupMap.get(key);
        const groupEl = document.createElement('div');
        groupEl.className = 'card-group';

        const totalQty = items.reduce(function(sum, item) {
            return sum + parseInt(item.dataset.quantity || '1', 10);
        }, 0);
        const header = document.createElement('h4');
        header.className = 'card-group-header';
        header.textContent = key + ' (' + totalQty + ')';
        groupEl.appendChild(header);

        const gallery = document.createElement('div');
        gallery.className = 'card-gallery';
        items.forEach(function(item) { gallery.appendChild(item); });
        groupEl.appendChild(gallery);

        cardList.appendChild(groupEl);
    });
}
