let dest_url = location.pathname
if (!dest_url.includes("_list")) {
    // If the path is a specific item, change it to the <item>_list url
    dest_url = dest_url.split("/", 3).join("/") + "_list/"
}
const menuItem = document.querySelector(`.navbar-nav > a[href$='${dest_url}'`);
if (menuItem) {
    menuItem.classList.add("active", "fw-semibold")
    menuItem.ariaCurrent = "page"
}