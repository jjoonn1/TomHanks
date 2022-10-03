import urllib
import bs4
from selenium import webdriver
import operator
import json
from threading import Thread


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs, Verbose)
        self._return = None

    def run(self):
        if self._Thread__target is not None:
            self._return = self._Thread__target(*self._Thread__args,
                                                **self._Thread__kwargs)

    def join(self):
        Thread.join(self)
        return self._return


def get_links_for_movies():
    chrome = webdriver.Chrome(executable_path=r"C:\code\KevinBacon\chromed2river.exe")
    chrome.get("http://www.imdb.com/name/nm0000158")
    chrome.find_element_by_id("show-actor").click()
    filmography = chrome.find_element_by_id("filmography")
    actor_filmography = filmography.find_element_by_xpath("//div[@id='filmo-head-actor']/following-sibling::div")
    films = actor_filmography.find_elements_by_xpath(".//b")
    hrefs = {}
    for film in films:
        if "(TV" in film.find_element_by_xpath("..").text.upper():
            continue
        link = film.find_element_by_xpath(".//a")
        hrefs[film.text] = link.get_attribute("href").split("?")[0]
    chrome.close()
    return hrefs


def get_cast(movie_link):
    webpage = urllib.urlopen(movie_link)
    htmlpage = bs4.BeautifulSoup(webpage, features='html.parser')
    full_cast_suffix = htmlpage.find(id="titleCast").find("div", {"class": "see-more"}).find("a").get("href")
    webpage = urllib.urlopen(movie_link + full_cast_suffix)
    htmlpage = bs4.BeautifulSoup(webpage, features="html.parser")
    cast_rows = htmlpage.find("table", {"class": "cast_list"}).find_all("tr")
    cast_rows.pop(0)
    cast_list = {}
    for actor in cast_rows:
        try:
            actor_a = actor.find_all("td")[1].find("a")
            cast_list[actor_a.get_text()] = get_num_of_oscars(actor_a.get("href"))
        except Exception as e:
            continue
    print "cast contains {} actors".format(len(cast_list))
    return cast_list


def get_num_of_oscars(href):
    webpage = urllib.urlopen("http://www.imdb.com" + href)
    htmlpage = bs4.BeautifulSoup(webpage, features='html.parser')
    try:
        awards = htmlpage.find("span", {"class": "awards-blurb"}).text
    except Exception as e:
        return 0
    if 'oscar' not in awards.lower() or "won" not in awards.lower():
        return 0
    return [int(word) for word in awards.split() if word.isdigit()][0]


def run_thread_on_subdict(subhref):
    print "entered thread"
    subset_of_actors = {}
    i = 1
    for name, href in subhref.items():
        print "movie #{}. {}".format(i, name)
        subset_of_actors.update(get_cast(href))
        i += 1
    return subset_of_actors


if __name__ == "__main__":
    hrefs = get_links_for_movies()
    sub_hrefs = [dict(hrefs.items()[len(hrefs)*i/5:len(hrefs)*(i+1)/5]) for i in xrange(5)]
    threads = []
    for sub_href in sub_hrefs:
        thread = ThreadWithReturnValue(target=run_thread_on_subdict, args=[sub_href])
        thread.start()
        threads.append(thread)

    actors_alongside = {}
    for thread in threads:
        actors_alongside.update(thread.join())

    actors_alongside = sorted(actors_alongside.items(), key=operator.itemgetter(1))
    with open(r"C:\code\KevinBacon\product.txt", "w") as product:
        json.dump(actors_alongside, product)
    print "done"


