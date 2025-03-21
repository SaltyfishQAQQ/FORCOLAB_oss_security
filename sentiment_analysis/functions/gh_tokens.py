# put your GitHub tokens here, should be classic tokens. Details on how to create them can be found here:
# https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#personal-access-tokens-classic

import os

tokens=os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

#if you have more than one token, you can put them in a string separated by commas
#tokens="token1,token2,token3"
