# twitter-network
Twitter accounts are connected to each other by following and being followed by other twitter accounts. For this project we put together some code that will allow you to visualize a chunk of this network.

Starting with an initial account name, a spider program will download all the friends (people that account follows) and save this list into a database. The spider will then read the next name in the database and download that account's friends list and so on. The spider will record which accounts are connected to each other in a separate table. 

Note that the free twitter API limits requests to pull friends to 200 at a time, with a 60 second delay between requests. This rate cap means that downloading the friends lists for some accounts is not practical because some accounts follow millions of other accounts. So we first check how many friends an account has and if it's over some limit, we skip that account.

Once we have a big enough database of accounts and connections, then we can start visualizing the network. We use the NetworkX python library to do the network visualization, however if our database is very large, then we will only be able to visualize a subset of the total network.
