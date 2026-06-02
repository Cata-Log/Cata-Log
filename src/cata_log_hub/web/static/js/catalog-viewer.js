const provider_id = document.getElementById("provider-id").dataset.id;

class Page {
  url = `/api/v1/providers/${provider_id}/catalogs/latest/pages/{page_number}/embed`;

  constructor(number) {
    this.number = number;
  }
  next() {
    return new Page(this.number + 1);
  }
  prev() {
    if (this.number === 0) {
      return this;
    }
    return new Page(this.number - 1);
  }
  preload() {
    let link = document.createElement("link");
    link.as = "image";
    link.rel = "preload";
    link.href = this.url.replace("{page_number}", this.number);
    document.head.append(link);
  }
  show() {
    pageImage.src = this.url.replace("{page_number}", this.number);
    pageImage.alt = `Page ${this.number}`;
  }
}

class DoublePage extends Page {
  constructor(number) {
    super(number);
    this.leftNumber = 2 * number;
    this.rightNumber = 2 * number + 1;
  }
  next() {
    return new DoublePage(this.number + 1);
  }
  prev() {
    if (this.number === 0) {
      return this;
    }
    return new DoublePage(this.number - 1);
  }
  preload() {
    let leftLink = document.createElement("link");
    leftLink.as = "image";
    leftLink.rel = "preload";
    leftLink.href = this.url.replace("{page_number}", this.leftNumber);
    document.head.append(leftLink);

    let rightLink = document.createElement("link");
    rightLink.as = "image";
    rightLink.rel = "preload";
    rightLink.href = this.url.replace("{page_number}", this.rightNumber);
    document.head.append(rightLink);
  }
  show() {
    rightPageImage.src = this.url.replace("{page_number}", this.rightNumber);
    rightPageImage.alt = `Page ${this.rightNumber}`;

    leftPageImage.src = this.url.replace("{page_number}", this.leftNumber);
    leftPageImage.alt = `Page ${this.leftNumber}`;
  }
}

currentPage = new Page(0);
currentDoublePage = new DoublePage(0);

pageImage = document.getElementById("page-image");
if (pageImage === null) {
  console.error("page image frame not found!");
}

document.addEventListener("DOMContentLoaded", () => {
  currentPage.show();
  currentPage.next().preload();
});

document.getElementById("next-button").addEventListener("click", () => {
  currentPage = currentPage.next();
  currentPage.show();
  currentPage.next().preload();
});
document.getElementById("prev-button").addEventListener("click", () => {
  currentPage = currentPage.prev();
  currentPage.show();
});

leftPageImage = document.getElementById("left-page-image");
rightPageImage = document.getElementById("right-page-image");
if (leftPageImage === null || rightPageImage === null) {
  console.error("page image frame not found!");
}

document.addEventListener("DOMContentLoaded", () => {
  currentDoublePage.show();
  currentDoublePage.next().preload();
});

document.getElementById("next-double-button").addEventListener("click", () => {
  currentDoublePage = currentDoublePage.next();
  currentDoublePage.show();
  currentDoublePage.next().preload();
});
document.getElementById("prev-double-button").addEventListener("click", () => {
  currentDoublePage = currentDoublePage.prev();
  currentDoublePage.show();
});
