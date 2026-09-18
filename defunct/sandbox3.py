
from my_functions import *
import os
import globals


os.chdir(os.path.dirname(os.path.abspath(__file__)))

#start_obs_then_record()
# resize_window_by_tuple(["sandbox"], region=globals.REGION_TOTAL_MINUS_MS_WINDOW, wait_for_window=3)
# resize_window_by_tuple(["SNAP"], region=globals.REGION_MS_WINDOW, wait_for_window=3)
#collect_cl_rewards()
# print(get_deck_card_names('666666'))
#print(get_series_shop_rewards())
# get_deck_card_names('666666')


click_any_MS_img(r'images/stages/main_stage/sign_out.png')
time.sleep(1)
click_any_MS_img(r'images/sign_out_grande.png')
# Se hace 2 veces en el mismo sign_out2 para deslogear correctamente
click_any_MS_img(r'images/stages/main_stage/sign_out2.png')
time.sleep(1)
click_any_MS_img(r'images/stages/main_stage/sign_out2_hover.png')

input('aea')