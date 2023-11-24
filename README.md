# Pythonic Websocket Server for Blackjack Gameplay

This API allows for stateful gameplay of Blackjack, accessible via a frontend.

## Components

This server is largely comprised of 3 modules
- Cards
    - Manages shoe / hand cards and includes important decorator functions for proactively updating card totals
    - Attaches a value, suit, and card to each individual card
- Player
    - Manages an individual player within the blackjack game
    - Valid moves, current value, splits, and hand results are all managed within this module
    - A player's cards wrap the `Cards` module above
- Game
    - Dictates the entire gameplay, manages the shoe, dealing, and tracks the count
    - Wraps the `Player` module for both the House and individual Players, of which both are created when a game round is initialized.
    - Wraps the `Cards` module to manage the Shoe and deals.
    - Rules are specified in this module, which dictate how `Player` acts in each game.

While the modules are all flexible enough to account for > 1 player, this websocket is simplified to only handle instances of 1 player. That is due to how I want the client to interact with the module, although it can easily be extended to account for more players and proper broadcasting back to clients.

## Websocket

The websocket route will spawn a specific instance of `Game`, as well as track a running `balance` (running profit) for that connected client. Also, it allows for asynchronous sending of messages, essentially server-side throttling + delay mechanism, which is managed through a `task` object.

The websocket will listen for the following states, as any websocket server would.

`on_connect()`

Simply adds the client to a global set of clients, which can be used for broadcasting (although this is not used, despite functionality being present). It'll send a message back to the client that they are connected and can initialize a game.

`on_receive()`

There are 5 distinct types of code that the server listens to from the client

- init
    - if `{code: "init"}` is received by the server, it'll also accept `rules` and `deck`, which tell the server how to initialize the `Game` module. These are not required, but each dictate the rules of gameplay, and some metadata around the deck
    - If successful, a message is sent back to the client that they are ready to begin gameplay
- reset
    - if `{code: "reset"}` is received, it simply wipes the `game` object and tells the client that it can restart the game. Acts almost identically to `on_connect()` message
- start
    - if `{code: "start"}` is received, it actually begins gameplay with an initialization of the round. It'll also accept a `wager` key/value pair, which is not required, but tells the game how many units are being wagered that round.
    - It'll deal the initial cards for both the player(s) and the house. If a player or the house draws a natural blackjack, the round is over, and additional logic follows.
    - Important state metrics are sent back to the client.
- step
    - if `{code: "step"}` is received, it'll also require a `move` key/value that tells the module which move that specific player is actually taking.
    - Game state is updated accordingly, then important state metrics are sent back to the client
    - If it's determined that the player is done for this round (either by having >= 21, doubling, staying, surrendering, or splitting Aces when the rules denote you can't draw again after splitting Aces), then additional logic is carried out.
    - This additional logic entails the house drawing cards until completion, and intermediate messages are sent async to the client with a time delay, as well as a message for the final state.
    - `balance` is updated accordingly based off the results.
- close
     - close the websocket connection after sending a message back to the client that it should reset the game state.


