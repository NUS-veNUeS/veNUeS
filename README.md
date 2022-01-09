<p align="center">
  <img src="https://user-images.githubusercontent.com/35778042/148596374-abae7ffd-0f39-4d27-8991-d8889d50d84e.png" />
</p>

## Inspiration
While studying for our finals, we realised that study spots in NUS are always taken up and we had to resort to finding empty rooms to study in. We made use of the venues feature on NUSMods to find such rooms but we found it inconvenient to use the website and there wasn't a feature to sort by the nearest study venues to our location. Using our phones to find the venues on the website can be quite a hassle as well due to the small screen size. Hence we decided to make it convenient to find venues through the use of a Telegram Bot, giving a more seamless experience.

## What it does
Provides numerous features that enable you to find a study venue that best caters to your needs:

1. **`/room`**
    - Checks the usage of specific study veNUeS provided by the user  
2. **`/locations`**
    - Provides a list of available veNUeS at a selected faculty/location along with their time of availability
3. **`/availability`** or **`/avail`**
    - Searches for the available veNUeS at a selected faculty/location during a given time period
4. **`/nearme`**
    - Finds 10 nearest available veNUeS to the user in a given time period

## How we built it
We made use of Telegram as our platform due to its popularity and ease of use! We made use of the Realtime Database provided by Firebase to store information about our venues and handled the logic using Python.

## Challenges we ran into
We had to preprocess the venue data given by the NUSMods API before we can make use of the data for our project. We also had to plan our database structure properly to avoid making too many changes further down the road. We tried to make things scalable as well, which was pretty challenging as we lack experience in planning. We also have to find ways to manage our API keys and deployment of the Telegram Bot.

## What's next for veNUeS
We plan to add more social features and expand the capabilities of searching! We hope to collaborate with NUS to allow students to book empty rooms to hold meetings, discussions, or study sessions.
