import pandas as pd
import logging
import os
import random

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

STUFF_DB_FILENAME = 'stuff.csv'

#TO DO: add db functions 
def create_new_stuff(chat_id, user, title, db_filename=STUFF_DB_FILENAME):
    
    if not os.path.exists(db_filename):
        stuff_df = pd.DataFrame(columns=['stuff_id', 'chat_id', 'username',
            'stuff_title', 'image_url']).set_index('stuff_id')
        stuff_id = 0
    else:
        stuff_df = pd.read_csv(db_filename).set_index('stuff_id')
        stuff_id = stuff_df.index.max() + 1

    new_stuff = pd.Series(
        data={
            'chat_id': chat_id, 
            'username': user,
            'stuff_title': title,
            'image_url': '',
        },
        name=stuff_id
    )
    new_stuff_df = stuff_df.append(new_stuff)
    new_stuff_df.to_csv(db_filename)


def add_photo_to_new_stuff(chat_id, photo_url, db_filename=STUFF_DB_FILENAME):
    stuff_df = pd.read_csv(db_filename).set_index('stuff_id')
    logger.info(stuff_df.head())
    stuff_id = stuff_df[stuff_df.chat_id == chat_id].index.max() 
    logger.info(f'STUFF_ID {stuff_id}')    
    logger.info(stuff_df.loc[stuff_id]['image_url'])
    stuff_df['image_url'][stuff_id] = photo_url
    logger.info(stuff_df.head())
    stuff_df.to_csv(db_filename)


def get_random_stuff(chat_id, db_filename=STUFF_DB_FILENAME):
    stuff_df = pd.read_csv(db_filename).set_index('stuff_id')
    logger.info(stuff_df.head())
    alias_stuff_df = stuff_df[stuff_df.chat_id != chat_id]
    logger.info(alias_stuff_df.index)
    if alias_stuff_df.empty:
        logger.info('NOT ANY')
        return None
    rand_index = random.choice(alias_stuff_df.index)
    logger.info(rand_index)
    rand_stuff = stuff_df.loc[rand_index]
    logger.info(rand_stuff) 
    return rand_stuff.name, rand_stuff["stuff_title"], rand_stuff["image_url"]


def main():
    # create_new_stuff(123456, 'yulya', 'вещь')
    # add_photo_to_new_stuff(123456, 'url')
    get_random_stuff(402274854)


if __name__ == '__main__':
    main()
