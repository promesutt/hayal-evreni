// Lens & Anlar - Photo Stream & Realtime Live Chat

document.addEventListener("DOMContentLoaded", () => {
  // Session & Identity
  let sessionId = localStorage.getItem("photo_portal_sess_id");
  if (!sessionId) {
    sessionId = "sess_" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("photo_portal_sess_id", sessionId);
  }

  const isAdmin = window.PORTAL_DATA?.isAdmin || false;
  const adminKey = window.PORTAL_DATA?.adminKey || "";

  let defaultName = localStorage.getItem("photo_portal_nickname") || (isAdmin ? "👑 Yönetici" : "Ziyaretçi " + Math.floor(100 + Math.random() * 900));
  if (isAdmin) defaultName = "👑 Yönetici";

  // Gallery State
  let photos = [];
  let currentSort = "newest";
  let searchQuery = "";
  let activeLightboxPhoto = null;

  // Chat State
  let lastMessageId = 0;
  let isChatOpen = false;
  let unreadCount = 0;
  let chatPollTimer = null;

  // DOM Elements - Gallery
  const galleryContainer = document.getElementById("galleryContainer");
  const emptyState = document.getElementById("emptyState");
  const loadingState = document.getElementById("loadingState");
  const searchInput = document.getElementById("searchInput");
  const sortSelect = document.getElementById("sortSelect");
  const pendingCountBadge = document.getElementById("pendingCountBadge");
  const headerOnlinePill = document.getElementById("headerOnlinePill");
  const headerOnlineText = document.getElementById("headerOnlineText");

  // DOM Elements - Modals
  const lightboxModal = document.getElementById("lightboxModal");
  const userUploadModal = document.getElementById("userUploadModal");
  const adminUploadModal = document.getElementById("adminUploadModal");
  const pendingModal = document.getElementById("pendingModal");
  const keyModal = document.getElementById("keyModal");

  // DOM Elements - Chat
  const chatToggleBtn = document.getElementById("chatToggleBtn");
  const chatBox = document.getElementById("chatBox");
  const btnMinimizeChat = document.getElementById("btnMinimizeChat");
  const chatMessages = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const chatInput = document.getElementById("chatInput");
  const chatSenderName = document.getElementById("chatSenderName");
  const chatNameRow = document.getElementById("chatNameRow");
  const chatOnlineStatus = document.getElementById("chatOnlineStatus");
  const chatOnlineBadge = document.getElementById("chatOnlineBadge");
  const chatUnreadBadge = document.getElementById("chatUnreadBadge");

  // Initialize Name in Chat Input
  if (chatSenderName) {
    if (isAdmin) {
      if (chatNameRow) chatNameRow.classList.add("hidden");
    } else {
      chatSenderName.value = defaultName;
      chatSenderName.addEventListener("change", () => {
        const val = chatSenderName.value.trim();
        if (val) {
          localStorage.setItem("photo_portal_nickname", val);
          defaultName = val;
        }
      });
    }
  }

  // Icons Helper
  const refreshIcons = () => {
    if (window.lucide) {
      window.lucide.createIcons();
    }
  };

  // Toast System
  const showToast = (message, type = "success") => {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `pointer-events-auto flex items-center gap-2 px-3.5 py-2.5 rounded-2xl text-xs font-semibold shadow-2xl border transition-all duration-300 transform translate-y-3 opacity-0 ${
      type === "success"
        ? "bg-neutral-900 border-emerald-500/40 text-emerald-300"
        : type === "error"
        ? "bg-neutral-900 border-rose-500/40 text-rose-300"
        : "bg-neutral-900 border-neutral-700 text-neutral-200"
    }`;

    const icon = type === "success" ? "check-circle-2" : type === "error" ? "alert-circle" : "info";
    toast.innerHTML = `<i data-lucide="${icon}" class="w-4 h-4 shrink-0"></i><span>${message}</span>`;
    container.appendChild(toast);
    refreshIcons();

    requestAnimationFrame(() => {
      toast.classList.remove("translate-y-3", "opacity-0");
    });

    setTimeout(() => {
      toast.classList.add("translate-y-3", "opacity-0");
      setTimeout(() => toast.remove(), 250);
    }, 3200);
  };

  // Modal Helpers
  const openModal = (modal) => {
    if (!modal) return;
    modal.classList.remove("hidden");
    requestAnimationFrame(() => modal.classList.add("modal-show"));
  };

  const closeModal = (modal) => {
    if (!modal) return;
    modal.classList.remove("modal-show");
    setTimeout(() => modal.classList.add("hidden"), 200);
  };

  document.querySelectorAll(".modal-close").forEach((btn) => {
    btn.addEventListener("click", () => closeModal(btn.closest(".fixed")));
  });

  // Fetch Pending Stats (for Admin badge)
  const fetchStats = async () => {
    if (!isAdmin) return;
    try {
      const res = await fetch("/api/stats");
      const data = await res.json();
      if (pendingCountBadge) {
        if (data.pending_count > 0) {
          pendingCountBadge.textContent = data.pending_count;
          pendingCountBadge.classList.remove("hidden");
        } else {
          pendingCountBadge.classList.add("hidden");
        }
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Fetch Photos in Unified Stream
  const fetchPhotos = async () => {
    if (loadingState) loadingState.classList.remove("hidden");
    if (emptyState) emptyState.classList.add("hidden");
    if (galleryContainer) galleryContainer.innerHTML = "";

    try {
      const url = new URL("/api/photos", window.location.origin);
      url.searchParams.set("sort", currentSort);
      if (searchQuery) url.searchParams.set("search", searchQuery);

      const res = await fetch(url.toString());
      const data = await res.json();
      photos = data.photos || [];

      renderGallery(photos);
    } catch (err) {
      console.error(err);
      showToast("Fotoğraflar yüklenemedi", "error");
    } finally {
      if (loadingState) loadingState.classList.add("hidden");
    }
  };

  // Render Gallery Stream
  const renderGallery = (items) => {
    if (!galleryContainer) return;
    galleryContainer.innerHTML = "";

    if (items.length === 0) {
      if (emptyState) emptyState.classList.remove("hidden");
      return;
    }
    if (emptyState) emptyState.classList.add("hidden");

    items.forEach((photo) => {
      const card = document.createElement("div");
      card.className = "photo-card group";
      card.dataset.id = photo.id;

      const isAdminPhoto = photo.uploader_role === "admin";
      const badgeHtml = isAdminPhoto
        ? `<span class="badge-admin inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold"><i data-lucide="crown" class="w-3 h-3"></i> Yönetici</span>`
        : `<span class="badge-user inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold"><i data-lucide="user" class="w-3 h-3"></i> ${photo.uploader_name}</span>`;

      let thumbSrc = photo.thumbnail || photo.filename;
      if (thumbSrc && thumbSrc.startsWith('http')) {
        // Cloudinary URL'sinde kare kırpma (c_fill) varsa, tam görsel için c_limit yap (asla kırpmaz)
        thumbSrc = thumbSrc.replace(/\/c_fill,[^/]+\//, '/c_limit,w_800,q_auto,f_auto/');
      } else {
        thumbSrc = '/static/thumbs/' + (photo.thumbnail || photo.filename);
      }

      card.innerHTML = `
        <div class="relative overflow-hidden bg-neutral-900 rounded-2xl">
          <img 
            src="${thumbSrc}" 
            alt="${photo.title || 'Fotoğraf'}" 
            loading="lazy" 
            class="w-full h-auto object-contain block rounded-2xl">
          
          <div class="photo-overlay rounded-2xl">
            <div class="flex items-center justify-between">
              ${badgeHtml}
              <button 
                class="btn-card-like p-2 rounded-full bg-neutral-900/80 hover:bg-neutral-800 text-rose-400 backdrop-blur-md transition-transform active:scale-125" 
                data-id="${photo.id}">
                <i data-lucide="heart" class="w-4 h-4 fill-current"></i>
              </button>
            </div>

            <div>
              <h4 class="text-white font-bold text-sm leading-snug drop-shadow truncate">${photo.title || 'İsimsiz'}</h4>
              <div class="flex items-center justify-between text-[11px] text-neutral-300 pt-1 border-t border-white/10 mt-1">
                <span>${isAdminPhoto ? '👑 Yönetici' : photo.uploader_name}</span>
                <span class="flex items-center gap-1 font-semibold text-rose-300">
                  <i data-lucide="heart" class="w-3 h-3 fill-current"></i>
                  <span class="card-like-count">${photo.likes_count || 0}</span>
                </span>
              </div>
            </div>
          </div>
        </div>
      `;

      // Open Lightbox on card click
      card.addEventListener("click", (e) => {
        if (e.target.closest(".btn-card-like")) return;
        openLightbox(photo);
      });

      // Like Button
      const likeBtn = card.querySelector(".btn-card-like");
      likeBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        likeBtn.classList.add("animate-pulse-heart");
        setTimeout(() => likeBtn.classList.remove("animate-pulse-heart"), 350);

        try {
          const res = await fetch(`/api/photos/${photo.id}/like`, { method: "POST" });
          const data = await res.json();
          if (data.success) {
            photo.likes_count = data.likes_count;
            card.querySelector(".card-like-count").textContent = data.likes_count;
          }
        } catch (err) {
          console.error(err);
        }
      });

      galleryContainer.appendChild(card);
    });

    refreshIcons();
  };

  // Lightbox
  const openLightbox = (photo) => {
    activeLightboxPhoto = photo;
    const imgEl = document.getElementById("lightboxImg");
    const titleEl = document.getElementById("lightboxTitle");
    const descEl = document.getElementById("lightboxDescription");
    const authorEl = document.getElementById("lightboxAuthor");
    const badgeEl = document.getElementById("lightboxBadge");
    const likeCountEl = document.getElementById("lightboxLikeCount");
    const downloadEl = document.getElementById("btnLightboxDownload");
    const deleteBtn = document.getElementById("btnLightboxDelete");

    const fullUrl = (photo.filename && photo.filename.startsWith('http')) ? photo.filename : `/static/uploads/${photo.filename}`;
    imgEl.src = fullUrl;
    imgEl.alt = photo.title || "Fotoğraf";
    titleEl.textContent = photo.title || "İsimsiz Fotoğraf";
    descEl.textContent = photo.description || "Fotoğraf açıklaması eklenmemiş.";
    authorEl.textContent = `Yükleyen: ${photo.uploader_name} • ${photo.created_at ? photo.created_at.slice(0, 10) : ''}`;
    likeCountEl.textContent = photo.likes_count || 0;
    downloadEl.href = fullUrl;
    downloadEl.setAttribute("download", photo.original_filename || photo.filename);

    if (photo.uploader_role === "admin") {
      badgeEl.className = "badge-admin inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold mb-3";
      badgeEl.innerHTML = `<i data-lucide="crown" class="w-3.5 h-3.5"></i> Yönetici Fotoğrafı`;
    } else {
      badgeEl.className = "badge-user inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold mb-3";
      badgeEl.innerHTML = `<i data-lucide="user" class="w-3.5 h-3.5"></i> Kullanıcı Fotoğrafı`;
    }

    if (isAdmin) {
      deleteBtn.classList.remove("hidden");
    } else {
      deleteBtn.classList.add("hidden");
    }

    openModal(lightboxModal);
    refreshIcons();
  };

  document.getElementById("btnCloseLightbox")?.addEventListener("click", () => {
    closeModal(lightboxModal);
  });

  // Lightbox Like
  document.getElementById("btnLightboxLike")?.addEventListener("click", async () => {
    if (!activeLightboxPhoto) return;
    try {
      const res = await fetch(`/api/photos/${activeLightboxPhoto.id}/like`, { method: "POST" });
      const data = await res.json();
      if (data.success) {
        activeLightboxPhoto.likes_count = data.likes_count;
        document.getElementById("lightboxLikeCount").textContent = data.likes_count;
        const card = document.querySelector(`.photo-card[data-id="${activeLightboxPhoto.id}"]`);
        if (card) {
          card.querySelector(".card-like-count").textContent = data.likes_count;
        }
      }
    } catch (e) {
      console.error(e);
    }
  });

  // Admin Delete from Lightbox
  document.getElementById("btnLightboxDelete")?.addEventListener("click", async () => {
    if (!activeLightboxPhoto || !isAdmin) return;
    if (!confirm("Bu fotoğrafı akıştan silmek istediğinize emin misiniz?")) return;

    try {
      const res = await fetch(`/api/admin/photo/${activeLightboxPhoto.id}`, { method: "DELETE" });
      const data = await res.json();
      if (data.success) {
        showToast("Fotoğraf silindi", "success");
        closeModal(lightboxModal);
        fetchPhotos();
        fetchStats();
      }
    } catch (err) {
      showToast("Silinemedi", "error");
    }
  });

  // Sort change
  sortSelect?.addEventListener("change", (e) => {
    currentSort = e.target.value;
    fetchPhotos();
  });

  // Search input
  let searchTimeout = null;
  searchInput?.addEventListener("input", (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      searchQuery = e.target.value.trim();
      fetchPhotos();
    }, 250);
  });

  // Unified Dropzone helper
  const setupDropzone = (dropzoneId, inputId, previewContainerId, previewImgId, nameElId) => {
    const dropzone = document.getElementById(dropzoneId);
    const input = document.getElementById(inputId);
    const previewContainer = document.getElementById(previewContainerId);
    const previewImg = document.getElementById(previewImgId);
    const nameEl = document.getElementById(nameElId);

    if (!dropzone || !input) return;

    const showPreview = (file) => {
      if (!file || !file.type.startsWith("image/")) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        previewImg.src = e.target.result;
        nameEl.textContent = file.name;
        previewContainer.classList.remove("hidden");
        dropzone.querySelector("#dropzonePrompt")?.classList.add("hidden");
      };
      reader.readAsDataURL(file);
    };

    input.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) showPreview(e.target.files[0]);
    });

    ["dragenter", "dragover"].forEach((evt) => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add("border-brand-500", "bg-brand-500/5");
      });
    });

    ["dragleave", "drop"].forEach((evt) => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove("border-brand-500", "bg-brand-500/5");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        input.files = e.dataTransfer.files;
        showPreview(e.dataTransfer.files[0]);
      }
    });
  };

  setupDropzone("dropzone", "fileInput", "previewContainer", "imgPreview", "fileName");

  // Open Unified Upload Modal
  const uploadModal = document.getElementById("uploadModal");
  document.getElementById("btnOpenUpload")?.addEventListener("click", () => {
    openModal(uploadModal);
    refreshIcons();
  });

  document.getElementById("btnEmptyUpload")?.addEventListener("click", () => {
    openModal(uploadModal);
    refreshIcons();
  });

  // Handle Unified Upload Form Submit (Directly Publishes to Stream)
  const uploadForm = document.getElementById("uploadForm");
  uploadForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("btnSubmitUpload");
    const origText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `<span class="animate-pulse">Yükleniyor...</span>`;

    try {
      const fd = new FormData(uploadForm);
      const res = await fetch("/api/upload", { method: "POST", body: fd });
      const data = await res.json();

      if (data.success) {
        showToast("Fotoğrafınız başarıyla yayınlandı!", "success");
        uploadForm.reset();
        document.getElementById("previewContainer")?.classList.add("hidden");
        document.getElementById("dropzonePrompt")?.classList.remove("hidden");
        closeModal(uploadModal);
        
        // Yeni fotoğrafı anında listenin başına ekle ve göster
        if (data.photo) {
          photos.unshift(data.photo);
          renderGallery(photos);
        } else {
          fetchPhotos();
        }
      } else {
        showToast(data.message || "Yükleme başarısız", "error");
      }
    } catch (err) {
      console.error(err);
      showToast("Bağlantı hatası oluştu", "error");
    } finally {
      btn.disabled = false;
      btn.innerHTML = origText;
      refreshIcons();
    }
  });


  // Admin Logout
  document.getElementById("btnAdminLogout")?.addEventListener("click", async () => {
    if (!confirm("Yönetici modundan çıkmak istiyor musunuz?")) return;
    await fetch("/api/admin/logout", { method: "POST" });
    window.location.href = "/";
  });

  // Key Modal
  document.getElementById("btnOpenKeyModal")?.addEventListener("click", () => {
    openModal(keyModal);
    document.getElementById("adminKeyInput")?.focus();
  });

  document.getElementById("keyForm")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const key = document.getElementById("adminKeyInput").value.trim();
    if (!key) return;
    const res = await fetch("/api/admin/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ key }),
    });
    const d = await res.json();
    if (d.success) {
      window.location.href = `/?admin_key=${encodeURIComponent(key)}`;
    } else {
      showToast("Hatalı anahtar", "error");
    }
  });

  // ==================== CANLI SOHBET & BİLDİRİMLER (SESLİ & GÖRSEL) ====================

  let isSoundEnabled = localStorage.getItem("photo_portal_sound") !== "false";
  let audioCtx = null;

  // Sesli Bildirim Üretici (Web Audio API - harici dosya gerektirmez, net ve zarif iki tonlu zil sesi)
  const playNotificationSound = () => {
    if (!isSoundEnabled) return;
    try {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
      const now = audioCtx.currentTime;

      // 1. Ton (784Hz - G5)
      const osc1 = audioCtx.createOscillator();
      const gain1 = audioCtx.createGain();
      osc1.type = 'sine';
      osc1.frequency.setValueAtTime(784, now);
      gain1.gain.setValueAtTime(0.18, now);
      gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.22);
      osc1.connect(gain1);
      gain1.connect(audioCtx.destination);
      osc1.start(now);
      osc1.stop(now + 0.22);

      // 2. Ton (1046Hz - C6)
      const osc2 = audioCtx.createOscillator();
      const gain2 = audioCtx.createGain();
      osc2.type = 'sine';
      osc2.frequency.setValueAtTime(1046, now + 0.08);
      gain2.gain.setValueAtTime(0.22, now + 0.08);
      gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.38);
      osc2.connect(gain2);
      gain2.connect(audioCtx.destination);
      osc2.start(now + 0.08);
      osc2.stop(now + 0.38);
    } catch (e) {
      console.log("Ses çalma uyarısı:", e);
    }
  };

  // Sekme Başlığı Yanıp Sönmesi (Görsel Bildirim)
  let titleFlashInterval = null;
  const originalDocTitle = "Hayal Evreni";
  const startTitleFlash = (senderName) => {
    if (titleFlashInterval) return;
    let isAlt = false;
    titleFlashInterval = setInterval(() => {
      document.title = isAlt ? `(💬 Yeni Mesaj!) Hayal Evreni` : `🔔 [${senderName}] - Hayal Evreni`;
      isAlt = !isAlt;
    }, 1000);
  };
  const stopTitleFlash = () => {
    if (titleFlashInterval) {
      clearInterval(titleFlashInterval);
      titleFlashInterval = null;
      document.title = originalDocTitle;
    }
  };
  window.addEventListener('focus', stopTitleFlash);

  // Tarayıcı / Masaüstü Bildirimi
  const requestNotificationPermission = () => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  };

  const showDesktopNotification = (senderName, messageText) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      if (document.hidden || !isChatOpen) {
        try {
          new Notification(`💬 ${senderName} (Hayal Evreni)`, {
            body: messageText,
            icon: '/static/thumbs/thumb_demo_1.webp'
          });
        } catch (e) {}
      }
    }
  };

  // Ses Açma / Kapatma Butonu
  const btnToggleSound = document.getElementById("btnToggleSound");
  const soundIcon = document.getElementById("soundIcon");
  const updateSoundUI = () => {
    if (!btnToggleSound || !soundIcon) return;
    if (isSoundEnabled) {
      btnToggleSound.classList.add("text-amber-400");
      btnToggleSound.classList.remove("text-neutral-500");
      btnToggleSound.title = "Sesli Bildirim Açık (Kapatmak için tıklayın)";
      soundIcon.setAttribute("data-lucide", "bell");
    } else {
      btnToggleSound.classList.remove("text-amber-400");
      btnToggleSound.classList.add("text-neutral-500");
      btnToggleSound.title = "Sesli Bildirim Kapalı (Açmak için tıklayın)";
      soundIcon.setAttribute("data-lucide", "bell-off");
    }
    refreshIcons();
  };

  btnToggleSound?.addEventListener("click", () => {
    isSoundEnabled = !isSoundEnabled;
    localStorage.setItem("photo_portal_sound", isSoundEnabled);
    updateSoundUI();
    requestNotificationPermission();
    if (isSoundEnabled) {
      playNotificationSound();
      showToast("🔔 Sesli bildirimler açıldı", "success");
    } else {
      showToast("🔕 Sesli bildirimler kapatıldı", "info");
    }
  });

  // İlk tıklamada ses motorunu ve bildirim iznini hazırla
  document.addEventListener('click', () => {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    requestNotificationPermission();
  }, { once: true });

  updateSoundUI();

  const toggleChat = () => {
    isChatOpen = !isChatOpen;
    if (isChatOpen) {
      chatBox.classList.remove("hidden");
      requestAnimationFrame(() => chatBox.classList.add("chat-show"));
      chatToggleBtn.classList.add("hidden");
      unreadCount = 0;
      updateUnreadBadge();
      stopTitleFlash();
      chatInput?.focus();
      scrollChatToBottom();
    } else {
      chatBox.classList.remove("chat-show");
      setTimeout(() => chatBox.classList.add("hidden"), 250);
      chatToggleBtn.classList.remove("hidden");
    }
  };

  chatToggleBtn?.addEventListener("click", toggleChat);
  btnMinimizeChat?.addEventListener("click", toggleChat);

  // Admin Tüm Sohbeti Temizleme Butonu
  const btnClearAllChat = document.getElementById("btnClearAllChat");
  if (isAdmin && btnClearAllChat) {
    btnClearAllChat.classList.remove("hidden");
    btnClearAllChat.addEventListener("click", async () => {
      if (!confirm("⚠️ Tüm sohbet geçmişini tek seferde silmek istediğinize emin misiniz?\n\nBu işlem geri alınamaz.")) return;
      try {
        const res = await fetch("/api/chat/messages/clear-all", {
          method: "DELETE",
          headers: adminKey ? { "X-Admin-Key": adminKey } : {}
        });
        const d = await res.json();
        if (d.success) {
          if (chatMessages) chatMessages.innerHTML = "";
          lastMessageId = 0;
          showToast("Tüm sohbet geçmişi temizlendi", "success");
        } else {
          showToast(d.message || "Sohbet temizlenemedi", "error");
        }
      } catch (err) {
        showToast("Hata oluştu", "error");
      }
    });
  }

  const updateUnreadBadge = () => {
    if (!chatUnreadBadge) return;
    if (unreadCount > 0 && !isChatOpen) {
      chatUnreadBadge.textContent = unreadCount;
      chatUnreadBadge.classList.remove("hidden");
    } else {
      chatUnreadBadge.classList.add("hidden");
    }
  };

  const scrollChatToBottom = () => {
    if (chatMessages) {
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  };

  const appendChatMessage = (msg, isHistorical = false) => {
    if (!chatMessages) return;

    // Duplication check
    if (chatMessages.querySelector(`[data-msg-id="${msg.id}"]`)) return;

    const row = document.createElement("div");
    row.className = "flex flex-col space-y-1";
    row.dataset.msgId = msg.id;

    const isSelf = msg.sender_name === (isAdmin ? "👑 Yönetici" : defaultName);
    const isAdminMsg = Boolean(msg.is_admin);

    let senderDisplay = msg.sender_name;
    if (isAdminMsg) {
      senderDisplay = `<span class="text-amber-400 font-bold inline-flex items-center gap-1"><i data-lucide="crown" class="w-3 h-3"></i> Yönetici</span>`;
    } else {
      senderDisplay = `<span class="text-neutral-400 font-medium">${msg.sender_name}</span>`;
    }

    const time = msg.created_at ? msg.created_at.slice(11, 16) : "";

    const deleteBtnHtml = isAdmin
      ? `<button class="btn-delete-msg p-1 text-neutral-500 hover:text-rose-400 rounded transition-colors ml-1" title="Mesajı Sil" data-id="${msg.id}">
           <i data-lucide="trash-2" class="w-3 h-3"></i>
         </button>`
      : '';

    row.innerHTML = `
      <div class="flex items-center gap-1.5 text-[10px] ${isSelf ? 'justify-end' : 'justify-start'}">
        ${!isSelf ? senderDisplay : ''}
        <span class="text-neutral-500">${time}</span>
        ${isSelf ? '<span class="text-brand-400 font-semibold">Sen</span>' : ''}
        ${deleteBtnHtml}
      </div>
      <div class="chat-bubble ${
        isSelf
          ? 'chat-bubble-self'
          : isAdminMsg
          ? 'chat-bubble-admin'
          : 'chat-bubble-user'
      }">
        ${escapeHtml(msg.message)}
      </div>
    `;

    // Admin message delete click handler
    if (isAdmin) {
      const delBtn = row.querySelector(".btn-delete-msg");
      delBtn?.addEventListener("click", async (e) => {
        e.stopPropagation();
        if (!confirm("Bu mesajı silmek istediğinize emin misiniz?")) return;
        try {
          const res = await fetch(`/api/chat/messages/${msg.id}`, { method: "DELETE" });
          const d = await res.json();
          if (d.success) {
            row.style.opacity = '0';
            row.style.transform = 'scale(0.9)';
            setTimeout(() => row.remove(), 200);
            showToast("Mesaj silindi", "success");
          } else {
            showToast("Mesaj silinemedi", "error");
          }
        } catch (err) {
          showToast("Hata oluştu", "error");
        }
      });
    }

    chatMessages.appendChild(row);

    if (!isHistorical) {
      if (!isSelf) {
        // Sesli bildirim çal
        playNotificationSound();

        // Görsel bildirimler (sekme başlığı yanıp sönmesi ve masaüstü bildirimi)
        if (document.hidden || !isChatOpen) {
          startTitleFlash(msg.sender_name);
          showDesktopNotification(msg.sender_name, msg.message);
        }
      }

      if (!isChatOpen) {
        unreadCount++;
        updateUnreadBadge();
      }
    }

    scrollChatToBottom();
    refreshIcons();
  };

  const escapeHtml = (str) => {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  };

  // Chat Polling
  const pollChatMessages = async () => {
    try {
      const activeName = isAdmin ? "👑 Yönetici" : (chatSenderName?.value.trim() || defaultName);
      const url = new URL("/api/chat/messages", window.location.origin);
      url.searchParams.set("after", lastMessageId);
      url.searchParams.set("session_id", sessionId);
      url.searchParams.set("username", activeName);

      const res = await fetch(url.toString());
      const data = await res.json();

      // Update online counters
      const count = data.online_count || 1;
      if (headerOnlineText) headerOnlineText.textContent = `${count} kişi aktif`;
      if (chatOnlineStatus) chatOnlineStatus.textContent = `${count} kişi sayfada aktif`;
      if (chatOnlineBadge) chatOnlineBadge.textContent = count;

      // Sync deleted messages in real time for all visitors
      if (data.active_ids && Array.isArray(data.active_ids) && lastMessageId > 0) {
        const activeSet = new Set(data.active_ids);
        chatMessages.querySelectorAll("[data-msg-id]").forEach((el) => {
          const mid = parseInt(el.dataset.msgId);
          if (!activeSet.has(mid)) {
            el.remove();
          }
        });
      }

      // Append new messages
      if (data.messages && data.messages.length > 0) {
        data.messages.forEach((msg) => {
          appendChatMessage(msg, lastMessageId === 0);
          if (msg.id > lastMessageId) {
            lastMessageId = msg.id;
          }
        });
      }
    } catch (e) {
      // quiet poll error
    }
  };

  // Send message
  chatForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    const sender = isAdmin ? "👑 Yönetici" : (chatSenderName?.value.trim() || defaultName);
    chatInput.value = "";

    try {
      const res = await fetch("/api/chat/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          sender_name: sender,
          session_id: sessionId,
        }),
      });
      const data = await res.json();
      if (data.success && data.message) {
        if (data.message.id > lastMessageId) {
          lastMessageId = data.message.id;
        }
        appendChatMessage(data.message, false);
      }
    } catch (err) {
      console.error(err);
      showToast("Mesaj gönderilemedi", "error");
    }
  });

  // Start polling every 1.5s
  pollChatMessages();
  chatPollTimer = setInterval(pollChatMessages, 1500);

  // Initial Load
  fetchPhotos();
  fetchStats();
  refreshIcons();

  // Escape key closes modals and chat
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      [lightboxModal, userUploadModal, adminUploadModal, pendingModal, keyModal].forEach(closeModal);
      if (isChatOpen) toggleChat();
    }
  });
});
