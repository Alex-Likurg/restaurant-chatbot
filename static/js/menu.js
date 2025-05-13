let tg = window.Telegram.WebApp;
tg.expand();

document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("menu-container");
    const modal = document.getElementById("imageModal");
    const modalImg = document.getElementById("modalImage");
    const span = document.querySelector(".modal-close");
    const prev = document.querySelector(".prev");
    const next = document.querySelector(".next");

    const imageUrls = [
        "/static/menu/main.jpg",
        "/static/menu/salat.jpg",
        "/static/menu/desert.jpg"
    ];
    let currentIndex = 0;

    // Показываем миниатюру
    const img = document.createElement("img");
    img.src = imageUrls[currentIndex];
    img.alt = "Меню ресторана";
    img.addEventListener("click", () => {
        modalImg.src = imageUrls[currentIndex];
        modal.style.display = "block";
    });
    container.appendChild(img);

    // Закрытие модалки
    span.onclick = () => {
        modal.style.display = "none";
    };

    window.onclick = (event) => {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    };

    // Перелистывание
    prev.onclick = () => {
        currentIndex = (currentIndex - 1 + imageUrls.length) % imageUrls.length;
        modalImg.src = imageUrls[currentIndex];
    };

    next.onclick = () => {
        currentIndex = (currentIndex + 1) % imageUrls.length;
        modalImg.src = imageUrls[currentIndex];
    };
});





//function loadMenu() {
  //  fetch("https://krasnayazvezda.store/api/get_menu")
     //   .then(response => response.json())
     //   .then(data => {
     //       if (data.status === "success") {
     //           let menuDiv = document.getElementById("menu-container");
     //           menuDiv.innerHTML = `<img src="${data.image_url}" alt="Меню" style="width:100%; max-width:400px; border-radius: 8px;">`;
     //       } else {
    //            document.getElementById("menu-container").innerHTML = `<p>❌ Ошибка загрузки меню.</p>`;
     //       }
      //  })
     //   .catch(error => {
     //       console.error("Ошибка загрузки меню:", error);
     //   });
//}

// document.addEventListener("DOMContentLoaded", loadMenu);

