// Cambiar entre modo oscuro y claro
document.getElementById('toggle-dark-mode').addEventListener('click', async () => {
    const isDarkMode = await window.darkMode.toggle();
    document.body.classList.toggle('dark-mode', isDarkMode);
    const icon = document.querySelector('#toggle-dark-mode i');
    icon.classList.toggle('fa-moon', !isDarkMode);
    icon.classList.toggle('fa-sun', isDarkMode);
});