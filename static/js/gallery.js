document.addEventListener("DOMContentLoaded", function () {
    const prevBtn = document.querySelector(".prev-btn");
    const nextBtn = document.querySelector(".next-btn");
    const videoContainer = document.querySelector(".videos");
    const videos = document.querySelectorAll(".videos iframe");

    let index = 0;
    const videosToShow = 3;
    const totalVideos = videos.length;
    const videoWidth = videos[0].offsetWidth + 15; // Ancho del video + gap
    const maxIndex = totalVideos - videosToShow;

    function updateCarousel() {
        videoContainer.style.transform = `translateX(${-index * videoWidth}px)`;
        checkButtons();
    }

    function checkButtons() {
        prevBtn.style.display = index === 0 ? "none" : "flex";
        nextBtn.style.display = index >= maxIndex ? "none" : "flex";
    }

    nextBtn.addEventListener("click", function () {
        if (index < maxIndex) {
            index++;
            updateCarousel();
        }
    });

    prevBtn.addEventListener("click", function () {
        if (index > 0) {
            index--;
            updateCarousel();
        }
    });

    checkButtons(); // Verificar botones al cargar
});   