async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function add_content(content) {
  jQuery(".content").append(content);
}

function generate_cover_block(info) {
  return '<div class="card"><a onclick="open_pdf(this)"><img src="data:image/png;base64,' +  info.cover_base64  +'" ' +
          'alt="' + info.id + '"></a></div>';
}

function block_content() {
  $(".content-blocker").toggleClass("hide")
}

async function add_del_favorite(author, title) {
  let exist = await eel.check_favorite(author, title)();
  if (exist) {
    await eel.del_stat("favorite", [author, title])();
  } else {
    await eel.stat_add("favorite", [author, title])();
  }
}

async function get_user_books() {
  let books_check = [];
  for (let book of await eel.get_stat("user_books")()) {
    books_check.push(book[0] + " " + book[1])
  }
  return books_check;
}

async function open_pdf(element) {
  block_content()
  let id_ = element.children[0]["alt"];
  let book_info = await eel.get_book_id(id_)();
  let content_h = $(".flex-body").find(".content-hidden")
  $(".points-block").removeClass("open")
  $(".menu").css("display", "none")

  $(".content").css("display", "none");
  content_h.css("display", "flex");
  content_h.html("<p style='color: aliceblue;\n" +
      "    display: flex;\n" +
      "    justify-content: center;\n" +
      "    font-size: 34px;'>Подготавливаем книгу...</p>");
  let link_pdf = await eel.open_pdf(book_info.author, book_info.title, book_info.category)();


  content_h.html("")
  $(".header").css("display", "none");
  $(".footer").css("display", "none");
  $(".header_pdf").css("display", "flex");
  $(".book-info").html("<p style='margin-bottom: 4px;'>Книга: " + book_info.title + "</p>" +
                      "<p>Автор: " + book_info.author + "</p>");
  document.getElementById("heart").setAttribute("onchange", "add_del_favorite('"+book_info.author+"', '"+book_info.title+"')");

  let book_trash = $("#del-book");
  if ((await get_user_books()).includes(book_info.author + " " + book_info.title)) {
    book_trash.css("display", "flex");
    book_trash.attr("onclick", "del_book('"+book_info.author+"', '"+book_info.title+"', '" + book_info.category + "')");
  } else {
    book_trash.css("display", "none");
    book_trash.attr("onclick", "")
  }

  let check_favorite = await eel.check_favorite(book_info.author, book_info.title)();
  if (check_favorite === true) {
    document.getElementById("heart").setAttribute("checked", "")
  }

  let height_pdf = $('.content-wrapper')[0].scrollHeight - 72;
  content_h.append("  <iframe\n" +
      "    src=\"/viewer_pdf/web/viewer.html?file=/" + link_pdf + "\"\n" +
      "    width=\"100%\"\n" +
      "    height=\"" + height_pdf + "px\"\n" +
      "    style=\"border: none;\" />");

  let block_add = ""

  content_h.css("background", "rgb(42, 42, 46)")

  block_add = "<div class=\"category-block\">\n" +
      "<p class=\"category-name\" style=\"text-align: center\">Похожее</p>\n" +
      "<div class=\"book-preview\">\n";
  let count = 0;
  let books_rec = await eel.get_recommendation(book_info.author, book_info.title, 5)()
  if (books_rec) {
      for (let book of books_rec) {
    if (count === 5) {
      block_add += "</div>\n</div>"
      count = 0
      content_h.append(block_add)
      block_add = "<div class=\"category-block\">\n" +
          "<div class=\"book-preview\">\n";
    }
    block_add += generate_cover_block(book);
    count += 1;
  }
  block_add += "</div>\n</div>";
  content_h.append(block_add);
  }
  block_content()
}

async function close_pdf() {
  let content_h = $(".flex-body").find(".content-hidden")
  document.getElementById("heart").removeAttribute("checked")
  content_h.css("background", "")
  $(".content").css("display", "flex");
  content_h.html("")
  content_h.css("display", "none");
  $(".header").css("display", "flex");
  $(".header_pdf").css("display", "none");
  $(".footer").css("display", "flex");
  $(".menu").css("display", "flex")
}

async function selected_fill() {
  let categories = await eel.all_categories()();
  let select_block = $("#add-book-form").find("#category")
  select_block.html("<option disabled selected>Выберите категорию</option>")
  for (let category of categories) {
    select_block.append("<option value='" + category + "'>" + category + "</option>")
  }
}

async function start_books() {
  let block_add = ""
  let load_block = $(".load_block")
  load_block.css("display", "flex")
  $("#content-block").html("")

  selected_fill()

  let recomendation = await eel.average_cosine_rec(5)();
  if (recomendation[0]) {
    block_add = "<div class=\"category-block\">\n" +
        "<p class=\"category-name category\" onclick='open_recommendation()'>Рекомендуем Вам</p>\n" +
        "<div class=\"book-preview\">\n"
    let c = 0
    for (let book of recomendation.reverse()) {
      if (c === 5) break
      block_add += generate_cover_block(book)
      c += 1
    }
    block_add += "</div>\n</div>";

    jQuery(".content").append(block_add);
  }

  // Отображение понравившихся книг
  let favorites = await eel.get_stat("favorite")();
  if (favorites[0]) {
    block_add = "<div class=\"category-block\">\n" +
        "<p class=\"category-name category\" onclick='open_favorite()'>Понравившиеся</p>\n" +
        "<div class=\"book-preview\">\n"
    let c = 0
    for (let book of favorites.reverse()) {
      if (c === 5) break
      let info = await eel.info_book(book[0], book[1])();
      block_add += generate_cover_block(info)
      c += 1
    }
    block_add += "</div>\n</div>";

    jQuery(".content").append(block_add);
  }

  // Добавление недавно просмотренных 5 книг (если есть)
  let viewed = await eel.get_viewed_books()();
  if (viewed[0]) {
    block_add = "<div class=\"category-block\">\n" +
        "<p class=\"category-name\">Недавно просмотренные</p>\n" +
        "<div class=\"book-preview\">\n"
    for (let book of viewed) {
      let info = await eel.info_book(book[0], book[1])();
      block_add += generate_cover_block(info)
    }
    block_add += "</div>\n</div>";

    jQuery(".content").append(block_add);
  }

  let menu_block = $(".points-block")
  menu_block.html("                <div class=\"cross-block\">\n" +
      "                    <span class=\"my-cross\"></span>\n" +
      "                    <button class=\"cross-btn\" onclick=\"move_menu();\"></button>\n" +
      "                </div>\n" +
      "                <div class=\"category-menu\">\n" +
      "                    <p id=\"category-name\" onclick=\"move_menu(); start_books()\">На главную</p>\n" +
      "                </div>")

  // Добавление рандомных книг из каждой категории
  let categories = await eel.all_categories()();
  for (let category of categories) {
    block_add = "<div class=\"category-block\">\n" +
        "<p class=\"category-name category\" onclick='open_category(\"" + category + "\", 0)'>" + category + "</p>\n" +
        "<div class=\"book-preview\">\n"
    for (let info of await eel.random_book_category(category)()) {
      block_add += generate_cover_block(info)
    }
    block_add += "</div>\n</div>";

    jQuery(".content").append(block_add);

    menu_block.append("<div class=\"category-menu\">\n" +
              "<p id=\"category-name\" onclick=\"move_menu(); open_category('" + category + "', 0)\">" + category + "</p>\n" +
                      "</div>")
  }
  menu_block.append("<div class=\"user-book\">\n" +
      "<p id=\"category-name\" onclick=\"open_user_books()\">Ваши книги</p>\n" +
      "</div>")
  load_block.css("display", "none")
}

async function search_book(e, query= "") {
  if ( query !== "" || (e.keyCode === 13 && this.search_query.value.length > 2)) {
    if (query === "") {
      let query = this.search_query.value
    } else {
      $(".results .books").html("");
      $(".results .authors").html("");
    }

    this.search_query.value = ""
    let ans = await eel.search_book(query)();
    let count = 0;
    let block_add = "";

    if (!ans[0] && !ans[1]) {
      this.search_query.value = "По вашему запросу ничего не найдено";
      await sleep(800)
      this.search_query.value = ""
      return false;
    }
    $(".content").html("")
    block_content()

    // Цикл отображения книг автора

    if (ans[0]) {
      block_add = "<div class=\"category-block\">\n" +
          "<p class=\"category-name\">Результаты поиска по автору: " + query + "</p>\n" +
          "<div class=\"book-preview\">\n";
      for (let book of ans[0]) {
        if (count === 5) {
          block_add += "</div>\n</div>"
          count = 0
          add_content(block_add)
          block_add = "<div class=\"category-block\">\n" +
                        "<div class=\"book-preview\">\n";
        }

        let info = await eel.info_book(query, book)();
        block_add += generate_cover_block(info)

        count += 1
      }
      block_add += "</div>\n</div>";

      jQuery(".content").append(block_add);
    }

    count = 0;
    // Цикл отображения книг с таким названием
    if (ans[1]) {
      block_add = "<div class=\"category-block\">\n" +
          "<p class=\"category-name\">Книги с похожим названием: " + query + "</p>\n" +
          "<div class=\"book-preview\">\n";
      for (let author of ans[1]) {
        if (count === 5) {
          block_add += "</div>\n</div>"
          count = 0
          add_content(block_add)
          block_add = "<div class=\"category-block\">\n" +
              "<div class=\"book-preview\">\n";
          count = 0
        }

        let info = await eel.info_book(author, query)();
        block_add += generate_cover_block(info)

        count += 1
      }
      block_add += "</div>\n</div>";

      jQuery(".content").append(block_add);
    }
    block_content()
    return false;
  }
}

async function open_add_book() {
  $(".add-book-page").css("display", "flex")
}

async function close_add_book() {
  $(".add-book-page").css("display", "none")
}

async function return_add_book_content() {
  $(".add-book-content").html("                <p class=\"add-book-title\">Форма добавления книги</p>\n" +
      "                <div id=\"add-book-form\">\n" +
      "                    <input class=\"input-book\" id=\"title\" type=\"text\" placeholder=\"Введите название\">\n" +
      "                    <input class=\"input-book\" id=\"author\" type=\"text\" placeholder=\"Введите имя автора\">\n" +
      "                    <select class=\"input-book\" id=\"category\">\n" +
      "                        <option disabled selected>Выберите категорию</option>\n" +
      "                    </select>\n" +
      "                    <div class=\"files-add\">\n" +
      "                        <input type=\"file\" id=\"text-file\" style=\"display: none;\" accept=\"text/*\">\n" +
      "                        <label for=\"text-file\" id=\"text-file-label\" class=\"label-text text-file\">Выберите текст книги</label>\n" +
      "\n" +
      "                        <input type=\"file\" id=\"cover-file\" style=\"display: none;\" accept=\"image/*\">\n" +
      "                        <label for=\"cover-file\" id=\"cover-file-label\" class=\"label-text cover-file\">Выберите обложку</label>\n" +
      "                    </div>\n" +
      "                    <button class=\"add-book-btn\" type=\"submit\" onclick=\"add_book()\">Добавить книгу</button>\n" +
      "                </div>")
}


async function add_book() {
  let text = document.getElementById("text-file-label")
  let cover = document.getElementById("cover-file-label")
  let author = document.getElementById("author")
  let title = document.getElementById("title")
  let category = $("#add-book-form").find("#category")
  let correct = true

  if (title.value.trim().length < 3) {title.style.borderColor = "red";correct = false;}
  if (author.value.trim().length < 3) {author.style.borderColor = "red";correct = false;}
  if (category.val() == null) {category.css("border-color", "red");correct = false;}
  if (document.getElementById("text-file").files[0] === undefined) {text.style.color = "red"; correct = false;}


  if (correct === false) {
    await sleep(1000)
    title.style.borderColor = ""
    author.style.borderColor = ""
    category.css("border-color", "")
    text.style.color = ""
    return
  }
  text = document.getElementById("text-file")
  cover = document.getElementById("cover-file")

  author = author.value.trim()
  title = title.value.trim()
  category = category.val()

  let book_info_add =  $(".add-book-content");

  var reader_text = new FileReader();
  reader_text.onload = async function () {
    var text = this.result;

    block_content()
    if (cover.files[0] === undefined)
    {

      book_info_add.html("<p class=\"successful\">Подождите загрузки книги на сервер</p>");
      let warn = await eel.add_book(author, title, text, category=category)();
      if (!warn) {
        book_info_add.html("<p class=\"successful\">Книга успешно добавлена</p>");
      } else {
        book_info_add.html("<p class=\"warn\">При добавлении книги произошла ошибка</p>");
      }

      await sleep(1200);
      await return_add_book_content();
      await close_add_book();
      window.location = "";

    }
    else
    {
      var reader_image = new FileReader();
      reader_image.onload = async function () {
        var image = this.result;

        book_info_add.html("<p class=\"successful\">Подождите загрузки книги на сервер</p>");
        let warn = await eel.add_book(author, title, text, category=category, cover=image)();
        if (!warn) {
          book_info_add.html("<p class=\"successful\">Книга успешно добавлена</p>");
        } else {
          book_info_add.html("<p class=\"warn\">При добавлении книги произошла ошибка</p>");
        }
        await sleep(1200);
        await return_add_book_content()
        await close_add_book();
        window.location = "";
      }
      reader_image.readAsDataURL(cover.files[0]);
    }
  }
  reader_text.readAsText(text.files[0]);
}

async function del_book(author, title, category) {
  await eel.del_book(author, title, category)();
  await sleep(300)
  await close_pdf()
  document.location.href = "index.html"
}

async function open_category(category, page) {
  block_content()

  if (page < 0) return false;
  let count_books = await eel.get_count_category(category)();
  let max_page_1 = 0
  if (count_books % 25 !== 0) max_page_1 = 1
  let max_page = Math.round((count_books / 25) - 0.5) + max_page_1
  if (page >= max_page) return false;

  page = parseInt(page);
  let books = await eel.books_category_paginated(category, page)();
  let block_add = "";

  $(".content").html("");
  block_add = "<div class=\"category-block\">\n" +
      "<p class=\"category-name\">" + category +"</p>\n" +
      "<div class=\"book-preview\">\n";
  let count = 0;
  for (let book of books) {
    if (count === 5) {
      block_add += "</div>\n</div>"
      count = 0
      await add_content(block_add)
      block_add = "<div class=\"category-block\">\n" +
          "<div class=\"book-preview\">\n";
    }
    block_add += generate_cover_block(book);
    count += 1;
  }
  block_add += "</div>\n</div>";
  await add_content(block_add);

  let next_page = page + 1;
  let prev_page = page - 1;

  await add_content("<div class='control-page'>" +
      "<div class='btn-prev-page' onclick='open_category(\"" + category + "\", " + prev_page + ")'></div>" +
      "<p class='page-info'>Страница " + next_page + " из " + max_page + "</p>" +
      "<div class='btn-next-page' onclick='open_category(\"" + category + "\", " + next_page + ")'></div>" +
                            "</div>");
  block_content()
}

async function open_favorite() {
  block_content()
  let books_ = await eel.get_stat("favorite")();
  let block_add = ""
  $(".content").html("");

  block_add = "<div class=\"category-block\">\n" +
      "<p class=\"category-name\">Все понравившиеся</p>\n" +
      "<div class=\"book-preview\">\n";
  let count = 0;
  for (let info_ of books_.reverse()) {
    if (count === 5) {
      block_add += "</div>\n</div>"
      count = 0
      await add_content(block_add)
      block_add = "<div class=\"category-block\">\n" +
          "<div class=\"book-preview\">\n";
    }
    block_add += generate_cover_block(await eel.info_book(info_[0], info_[1])());
    count += 1;
  }
  block_add += "</div>\n</div>";
  await add_content(block_add);
  block_content()
}

async function open_recommendation() {
  block_content()
  let books_info = await eel.average_cosine_rec(25)();
  let block_add = ""
  $(".content").html("");

  block_add = "<div class=\"category-block\">\n" +
      "<p class=\"category-name\">Рекомендации</p>\n" +
      "<div class=\"book-preview\">\n";
  let count = 0;
  for (let info of books_info.reverse()) {
    if (count === 5) {
      block_add += "</div>\n</div>"
      count = 0
      await add_content(block_add)
      block_add = "<div class=\"category-block\">\n" +
          "<div class=\"book-preview\">\n";
    }
    block_add += generate_cover_block(info);
    count += 1;
  }
  block_add += "</div>\n</div>";
  await add_content(block_add);
  block_content()
}

async function open_user_books() {
  block_content()
  let books_info = await eel.get_user_book_info()();
  let block_add = ""
  $(".content").html("");

  block_add = "<div class=\"category-block\">\n" +
      "<p class=\"category-name\">Ваши книги</p>\n" +
      "<div class=\"book-preview\">\n";
  let count = 0;
  for (let info of books_info.reverse()) {
    if (count === 5) {
      block_add += "</div>\n</div>"
      count = 0
      await add_content(block_add)
      block_add = "<div class=\"category-block\">\n" +
          "<div class=\"book-preview\">\n";
    }
    block_add += generate_cover_block(info);
    count += 1;
  }
  block_add += "</div>\n</div>";
  await add_content(block_add);
  block_content()
}

function move_menu() {
  $(".points-block").toggleClass("open")
}

let result_search_block = $("#search_query")

result_search_block.focus(function() {
  $(".results").toggleClass("hide")
});

result_search_block.blur(async function() {
  await sleep(200)
  $(".results").toggleClass("hide")
});

async function debounce_search() {
  let element = $("#search_query")
  let book_chapter =  $(".results .books")
  let author_chapter  = $(".results .authors")

  if (element.val() !== "") {
    let query_search = await eel.fast_search(element.val())();
    let authors = query_search.authors;
    let titles = query_search.titles;

    if (!authors[0] && !titles[0]) {
      book_chapter.addClass("hide");
      author_chapter.addClass("hide");

      return false;
    }

    if (authors[0] !== []) book_chapter.removeClass("hide");
    if (titles[0] !== []) author_chapter.removeClass("hide");


    let authors_add = "<p>Авторы:</p>";
    let titles_add = "<p>Книги:</p>";
    for (let title of titles) {
      titles_add += "<p onclick='search_book(this, \"" + title + "\")'>" + title + "</p>";
    }
    for (let author of authors) {
      authors_add += "<p onclick='search_book(this, \"" + author + "\")'>" + author + "</p>";
    }

    book_chapter.html(titles_add);
    author_chapter.html(authors_add);

  } else {
    book_chapter.addClass("hide");
    author_chapter.addClass("hide");

    book_chapter.html("<p>Книги:</p>");
    author_chapter.html("<p>Авторы:</p>");
  }
}

const debounce = function (fn, d) {
  let timer;
  return function () {
    let context = this, args = arguments;
    clearTimeout(timer);
    timer = setTimeout(() => {
      fn.apply(context, args);
    }, d)
  }
}

const debounceForData = debounce(debounce_search, 400);

start_books()