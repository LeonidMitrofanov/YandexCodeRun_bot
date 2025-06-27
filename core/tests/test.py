import parser
import analytics
import bot

def test_parser():
    scraper = parser.CodeRunRatingScraper(languages=['c','c-sharp'])
    scraper.update()
    scraper.save('test', 'csv')


if __name__ == "__main__":
    test_parser()