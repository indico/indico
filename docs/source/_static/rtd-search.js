// Enable RTD search
// See: https://docs.readthedocs.com/platform/stable/addons.html#integrate-with-search-as-you-type
document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('.sidebar-search')?.addEventListener('click', () => {
        document.dispatchEvent(new CustomEvent('readthedocs-search-show'));
    });
});
