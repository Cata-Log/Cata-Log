provider_id = document.getElementById("provider-id").dataset.id;
page_url = `/api/v1/providers/${provider_id}/catalogs/latest/pages/{page_number}/embed`;

page_number = 0;

pageImage = document.getElementById("page-image");
if (pageImage === null) {
  console.error("page image frame not found!");
}

document.addEventListener("DOMContentLoaded", () => {
  showPage();
  preloadNextPage();
});

document.getElementById("next-button").addEventListener("click", () => {
  showNextPage();
  preloadNextPage();
});
document.getElementById("prev-button").addEventListener("click", () => {
  showPrevPage();
});

function preloadNextPage() {
  link = document.createElement("link");
  link.as = "image";
  link.rel = "preload";
  link.href = page_url.replace("{page_number}", page_number + 1);
  document.head.append(link);
}

function showPage() {
  pageImage.src = page_url.replace("{page_number}", page_number);
  pageImage.alt = `Page ${page_number}`;
}

function showNextPage() {
  page_number++;
  showPage();
}

function showPrevPage() {
  if (page_number === 0) {
    return;
  }
  page_number--;
  showPage();
}
