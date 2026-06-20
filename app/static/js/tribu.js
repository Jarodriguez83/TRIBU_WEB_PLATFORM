/* ==========================================================================
   LÓGICA DEL CLIENTE - CARRITO, MENÚ MÓVIL Y NOTIFICACIONES - TRIBU STORE
   ========================================================================== */

document.addEventListener("DOMContentLoaded", function() {
    // Inicializar componentes globales
    initMobileMenu();
    updateCartBadge();
    
    // Identificar qué página se está cargando
    const path = window.location.pathname;
    
    if (path.includes("/producto/")) {
        initProductDetailPage();
    } else if (path === "/carrito" || path === "/carrito/") {
        renderCartPage();
    } else if (path === "/checkout" || path === "/checkout/") {
        initCheckoutPage();
    }
});

/* ==========================================================================
   MENÚ MÓVIL (DRAWER)
   ========================================================================== */
function initMobileMenu() {
    const menuToggle = document.getElementById("menu-toggle");
    const mobileDrawer = document.getElementById("mobile-drawer");
    const drawerClose = document.getElementById("drawer-close");
    const drawerOverlay = document.getElementById("drawer-overlay");

    if (menuToggle && mobileDrawer && drawerClose && drawerOverlay) {
        const toggleMenu = () => {
            mobileDrawer.classList.toggle("open");
            drawerOverlay.classList.toggle("open");
        };

        menuToggle.addEventListener("click", toggleMenu);
        drawerClose.addEventListener("click", toggleMenu);
        drawerOverlay.addEventListener("click", toggleMenu);
    }
}

/* ==========================================================================
   SISTEMA DE NOTIFICACIONES (TOASTS)
   ========================================================================== */
function showToast(message, type = "success") {
    const container = document.getElementById("notification-container");
    if (!container) return;
    
    // Crear elemento toast
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    
    // Icono correspondiente
    let icon = '<i class="fa-solid fa-circle-check"></i>';
    if (type === "error") {
        icon = '<i class="fa-solid fa-circle-exclamation"></i>';
    } else if (type === "warning") {
        icon = '<i class="fa-solid fa-triangle-exclamation"></i>';
    }
    
    toast.innerHTML = `${icon} <span>${message}</span>`;
    container.appendChild(toast);
    
    // Animación de entrada
    setTimeout(() => {
        toast.classList.add("show");
    }, 10);
    
    // Eliminación automática tras 3.5 segundos
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3500);
}

/* ==========================================================================
   GESTIÓN DE CARRITO (LOCALSTORAGE)
   ========================================================================== */
const CART_KEY = "tribu_cart";

function getCart() {
    try {
        const cartStr = localStorage.getItem(CART_KEY);
        return cartStr ? JSON.parse(cartStr) : [];
    } catch (e) {
        return [];
    }
}

function saveCart(cart) {
    localStorage.setItem(CART_KEY, JSON.stringify(cart));
    updateCartBadge();
}

function updateCartBadge() {
    const badge = document.getElementById("cart-badge");
    if (!badge) return;
    
    const cart = getCart();
    const totalItems = cart.reduce((sum, item) => sum + item.cantidad, 0);
    badge.textContent = totalItems;
}

function addToCart(id, nombre, precio, imagen, talla, cantidad) {
    let cart = getCart();
    
    // Buscar si ya existe el mismo artículo con la misma talla
    const existingIndex = cart.findIndex(item => item.id === id && item.talla === talla);
    
    if (existingIndex > -1) {
        cart[existingIndex].cantidad += cantidad;
    } else {
        cart.push({
            id: id,
            nombre: nombre,
            precio: parseFloat(precio),
            imagen: imagen,
            talla: talla,
            cantidad: cantidad
        });
    }
    
    saveCart(cart);
    showToast(`¡${nombre} (${talla}) agregado al carrito!`, "success");
}

function removeFromCart(id, talla) {
    let cart = getCart();
    const item = cart.find(i => i.id === id && i.talla === talla);
    
    cart = cart.filter(i => !(i.id === id && i.talla === talla));
    saveCart(cart);
    
    if (item) {
        showToast(`Removido: ${item.nombre} (${talla})`, "warning");
    }
}

function updateQuantity(id, talla, newQty) {
    let cart = getCart();
    const index = cart.findIndex(i => i.id === id && i.talla === talla);
    
    if (index > -1) {
        cart[index].cantidad = Math.max(1, newQty);
        saveCart(cart);
    }
}

/* ==========================================================================
   PÁGINA DE DETALLE DE PRODUCTO
   ========================================================================== */
function initProductDetailPage() {
    const btnAdd = document.getElementById("btn-add-cart");
    const qtyMinus = document.getElementById("qty-minus");
    const qtyPlus = document.getElementById("qty-plus");
    const qtyInput = document.getElementById("qty-input");
    const sizeError = document.getElementById("size-error");
    const priceEl = document.getElementById("detail-price");
    
    if (!btnAdd) return;
    
    const maxStock = parseInt(qtyInput ? qtyInput.getAttribute("max") : 1);
    
    // Controles de cantidad
    if (qtyMinus && qtyPlus && qtyInput) {
        qtyMinus.addEventListener("click", () => {
            let val = parseInt(qtyInput.value);
            if (val > 1) qtyInput.value = val - 1;
        });
        
        qtyPlus.addEventListener("click", () => {
            let val = parseInt(qtyInput.value);
            if (val < maxStock) qtyInput.value = val + 1;
        });
    }
    
    // Botón Agregar al Carrito
    btnAdd.addEventListener("click", () => {
        // Obtener talla seleccionada
        const sizeRadio = document.querySelector('input[name="talla"]:checked');
        
        if (!sizeRadio) {
            if (sizeError) sizeError.style.display = "block";
            showToast("Por favor selecciona una talla antes de continuar.", "error");
            return;
        }
        
        if (sizeError) sizeError.style.display = "none";
        
        const id = btnAdd.getAttribute("data-id");
        const nombre = btnAdd.getAttribute("data-nombre");
        const precio = parseFloat(priceEl.getAttribute("data-price"));
        const imagen = btnAdd.getAttribute("data-imagen");
        const talla = sizeRadio.value;
        const cantidad = parseInt(qtyInput.value);
        
        addToCart(id, nombre, precio, imagen, talla, cantidad);
    });
    
    // Quitar alerta de error si selecciona talla
    const sizeRadios = document.querySelectorAll('input[name="talla"]');
    sizeRadios.forEach(radio => {
        radio.addEventListener("change", () => {
            if (sizeError) sizeError.style.display = "none";
        });
    });
}

/* ==========================================================================
   PÁGINA DE CARRITO DE COMPRAS
   ========================================================================== */
function renderCartPage() {
    const emptyView = document.getElementById("cart-empty-view");
    const contentView = document.getElementById("cart-content-view");
    const itemsList = document.getElementById("cart-items-list");
    const subtotalEl = document.getElementById("summary-subtotal");
    const totalEl = document.getElementById("summary-total");
    
    if (!itemsList) return;
    
    const cart = getCart();
    
    if (cart.length === 0) {
        if (emptyView) emptyView.style.display = "block";
        if (contentView) contentView.style.display = "none";
        return;
    }
    
    if (emptyView) emptyView.style.display = "none";
    if (contentView) contentView.style.display = "grid";
    
    itemsList.innerHTML = "";
    let subtotal = 0.0;
    
    cart.forEach(item => {
        const itemTotal = item.precio * item.cantidad;
        subtotal += itemTotal;
        
        const row = document.createElement("div");
        row.className = "cart-item";
        row.innerHTML = `
            <img src="${item.imagen}" alt="${item.nombre}" class="cart-item-image">
            <div class="cart-item-info">
                <span class="cart-item-title">${item.nombre}</span>
                <span class="cart-item-meta">Talla: ${item.talla}</span>
                <span class="cart-item-price">$${formatCOP(item.precio)} COP</span>
            </div>
            <div class="cart-item-qty">
                <div class="quantity-selector" style="transform: scale(0.85);">
                    <button class="qty-btn btn-qty-minus" data-id="${item.id}" data-talla="${item.talla}"><i class="fa-solid fa-minus"></i></button>
                    <input type="number" class="qty-input-field" value="${item.cantidad}" readonly style="width: 35px;">
                    <button class="qty-btn btn-qty-plus" data-id="${item.id}" data-talla="${item.talla}"><i class="fa-solid fa-plus"></i></button>
                </div>
            </div>
            <div style="font-family: var(--font-heading); font-weight: 700; min-width: 100px; text-align: right;">
                $${formatCOP(itemTotal)}
            </div>
            <button class="btn-remove-item" data-id="${item.id}" data-talla="${item.talla}">
                <i class="fa-solid fa-trash-can"></i>
            </button>
        `;
        itemsList.appendChild(row);
    });
    
    // Actualizar resumen
    subtotalEl.textContent = `$${formatCOP(subtotal)} COP`;
    totalEl.textContent = `$${formatCOP(subtotal)} COP`; // En esta página el envío aún no se ha sumado
    
    // Conectar eventos
    connectCartEvents();
}

function connectCartEvents() {
    // Botones quitar item
    document.querySelectorAll(".btn-remove-item").forEach(btn => {
        btn.addEventListener("click", () => {
            const id = btn.getAttribute("data-id");
            const talla = btn.getAttribute("data-talla");
            removeFromCart(id, talla);
            renderCartPage();
        });
    });
    
    // Cantidades
    document.querySelectorAll(".btn-qty-minus").forEach(btn => {
        btn.addEventListener("click", () => {
            const id = btn.getAttribute("data-id");
            const talla = btn.getAttribute("data-talla");
            const cart = getCart();
            const item = cart.find(i => i.id === id && i.talla === talla);
            if (item && item.cantidad > 1) {
                updateQuantity(id, talla, item.cantidad - 1);
                renderCartPage();
            }
        });
    });
    
    document.querySelectorAll(".btn-qty-plus").forEach(btn => {
        btn.addEventListener("click", () => {
            const id = btn.getAttribute("data-id");
            const talla = btn.getAttribute("data-talla");
            const cart = getCart();
            const item = cart.find(i => i.id === id && i.talla === talla);
            if (item) {
                updateQuantity(id, talla, item.cantidad + 1);
                renderCartPage();
            }
        });
    });
}

/* ==========================================================================
   PÁGINA DE CHECKOUT (ENVÍO Y ENVÍO DINÁMICO)
   ========================================================================== */
function initCheckoutPage() {
    const listContainer = document.getElementById("checkout-products-list");
    const subtotalEl = document.getElementById("checkout-subtotal");
    const shippingEl = document.getElementById("checkout-shipping");
    const totalEl = document.getElementById("checkout-total");
    
    const deptoSelect = document.getElementById("departamento");
    const ciudadSelect = document.getElementById("ciudad");
    const form = document.getElementById("checkout-form");
    const cartDataInput = document.getElementById("cart-data-input");
    
    const cart = getCart();
    
    if (cart.length === 0) {
        window.location.href = "/catalogo";
        return;
    }
    
    // Rellenar lista del checkout
    if (listContainer) {
        listContainer.innerHTML = "";
        let subtotal = 0.0;
        
        cart.forEach(item => {
            subtotal += item.precio * item.cantidad;
            const row = document.createElement("div");
            row.className = "checkout-product-item";
            row.innerHTML = `
                <span>${item.nombre} (Talla: ${item.talla}) <strong>x${item.cantidad}</strong></span>
                <span>$${formatCOP(item.precio * item.cantidad)} COP</span>
            `;
            listContainer.appendChild(row);
        });
        
        subtotalEl.textContent = `$${formatCOP(subtotal)} COP`;
        
        // Manejador del select de departamentos para habilitar ciudades y calcular envío
        if (deptoSelect && ciudadSelect) {
            deptoSelect.addEventListener("change", () => {
                const deptoSelected = deptoSelect.value;
                const deptoInfo = DEPTOS_DATA[deptoSelected];
                
                // Vaciar y activar select de ciudades
                ciudadSelect.innerHTML = '<option value="" disabled selected>Selecciona tu ciudad</option>';
                ciudadSelect.disabled = false;
                
                deptoInfo.ciudades.forEach(ciudad => {
                    const opt = document.createElement("option");
                    opt.value = ciudad;
                    opt.textContent = ciudad;
                    ciudadSelect.appendChild(opt);
                });
                
                // Actualizar envío en la vista
                const costoEnvio = deptoInfo.envio;
                shippingEl.textContent = `$${formatCOP(costoEnvio)} COP`;
                
                const totalFinal = subtotal + costoEnvio;
                totalEl.textContent = `$${formatCOP(totalFinal)} COP`;
            });
        }
        
        // Inyectar datos del carrito en el input hidden antes de enviar
        if (form && cartDataInput) {
            form.addEventListener("submit", (e) => {
                // Serializa el carrito actual y lo pone en el formulario
                cartDataInput.value = JSON.stringify(getCart());
            });
        }
    }
}

/* ==========================================================================
   UTILIDADES
   ========================================================================== */
function formatCOP(number) {
    return new Intl.NumberFormat("es-CO", {
        minimumFractionDigits: 0
    }).format(number);
}
