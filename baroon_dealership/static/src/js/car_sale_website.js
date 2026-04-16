document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('carLightboxModal');
    const modalImage = document.querySelector('.js-car-lightbox-image');
    const mainImage = document.querySelector('.js-car-main-image');
    let zoom = 1;

    const applyZoom = () => {
        if (modalImage) {
            modalImage.style.transform = `scale(${zoom})`;
        }
        const resetButton = document.querySelector('.js-zoom-reset');
        if (resetButton) {
            resetButton.textContent = `${Math.round(zoom * 100)}%`;
        }
    };

    const openModal = () => {
        if (!modal || !modalImage || !mainImage) return;
        modalImage.src = mainImage.dataset.full || mainImage.src;
        zoom = 1;
        applyZoom();
        modal.classList.add('is-open');
    };

    const closeModal = () => {
        if (!modal || !modalImage) return;
        modal.classList.remove('is-open');
        modalImage.src = '';
        zoom = 1;
        applyZoom();
    };

    const setMainImage = (src) => {
        if (!mainImage || !src) return;
        mainImage.src = src;
        mainImage.dataset.full = src;
    };

    const activateThumb = (thumb) => {
        if (!thumb) return;
        const src = thumb.dataset.full || thumb.dataset.src;
        if (!src) return;
        setMainImage(src);
        document.querySelectorAll('.js-car-thumb').forEach((el) => el.classList.remove('is-active'));
        thumb.classList.add('is-active');
        try {
            thumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        } catch (_) {}
    };

    document.querySelectorAll('.js-car-thumb').forEach((thumb) => {
        thumb.addEventListener('click', (ev) => {
            ev.preventDefault();
            activateThumb(thumb);
        });
    });

    document.querySelectorAll('.js-open-car-lightbox, .js-car-main-image').forEach((el) => {
        el.addEventListener('click', (ev) => {
            ev.preventDefault();
            openModal();
        });
    });

    document.querySelectorAll('.js-close-car-lightbox').forEach((btn) => {
        btn.addEventListener('click', (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            closeModal();
        });
    });

    document.querySelectorAll('.js-zoom-in').forEach((btn) => {
        btn.addEventListener('click', (ev) => {
            ev.preventDefault();
            zoom = Math.min(zoom + 0.2, 3);
            applyZoom();
        });
    });

    document.querySelectorAll('.js-zoom-out').forEach((btn) => {
        btn.addEventListener('click', (ev) => {
            ev.preventDefault();
            zoom = Math.max(zoom - 0.2, 0.6);
            applyZoom();
        });
    });

    document.querySelectorAll('.js-zoom-reset').forEach((btn) => {
        btn.addEventListener('click', (ev) => {
            ev.preventDefault();
            zoom = 1;
            applyZoom();
        });
    });

    if (modal) {
        modal.addEventListener('click', (ev) => {
            if (ev.target === modal || ev.target.classList.contains('car-lightbox-stage')) {
                closeModal();
            }
        });
    }

    if (modalImage) {
        modalImage.addEventListener('wheel', (ev) => {
            ev.preventDefault();
            zoom = ev.deltaY < 0 ? Math.min(zoom + 0.1, 3) : Math.max(zoom - 0.1, 0.6);
            applyZoom();
        });
    }

    document.addEventListener('keydown', (ev) => {
        if (!modal || !modal.classList.contains('is-open')) return;
        if (ev.key === 'Escape') {
            closeModal();
        } else if (ev.key === '+') {
            zoom = Math.min(zoom + 0.2, 3);
            applyZoom();
        } else if (ev.key === '-') {
            zoom = Math.max(zoom - 0.2, 0.6);
            applyZoom();
        }
    });
});
