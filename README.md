# Joseki-Scraper
A script for scraping the joseki from Go games.

Currently, the script is designed for (and likely only works on) OGS's JSON game dumps. The games can be found in an OGS database dump [here](https://forums.online-go.com/t/can-we-get-an-sgf-database-dump/38837).

The algorithm itself is based on a research paper by Carson Liang, Felix Kanke, and Alfredo Cuzzocrea, titled ["Data analytics on the board game Go for the discovery of interesting sequences of moves in joseki"](https://www.researchgate.net/publication/327289473_Data_analytics_on_the_board_game_Go_for_the_discovery_of_interesting_sequences_of_moves_in_joseki).

## Running the script
Requires the [tqdm](https://pypi.org/project/tqdm/) progress bar library by default, but this results in no direct functionality change and occurrences of `tqdm` can safely be removed.

At the bottom of the included python file, configure the script to take input from and output to whatever files you prefer. It's currently configured for having OGS's `sample-100k.json` in a nearby file. It will follow steps from reading the raw games to outputting the variation tree in SGF format, sorted by frequency.

## To-do:
- Handle more types of input, most notably SGF input.
- Improve joseki detection algorithm.
