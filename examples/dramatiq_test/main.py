from examples.dramatiq_test.count_words import count_words

if __name__ == '__main__':
    urls = [
        "https://news.ycombinator.com",
        "https://xkcd.com",
        "https://rabbitmq.com",
    ]
    [count_words.send(url) for url in urls]