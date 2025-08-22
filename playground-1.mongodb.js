/* global use, db */
// MongoDB Playground
// Use Ctrl+Space inside a snippet or a string literal to trigger completions.

const database = 'utkalLabs';

use(database);
db.botQuestion.find({name:{"$ne": null}}).toArray().length;

// db.botQuestion.insertMany([
//   {
//     sequence: 1,
//     text: "What is your name?",
//     type: "text",
//     options: null,
//     name: "Name"
//   },
//   {
//     sequence: 2,
//     text: "What is your email?",
//     type: "text",
//     options: null,
//     name: "Email"
//   },
//   {
//     sequence: 3,
//     text: "What is your phone number?",
//     type: "text",
//     options: null,
//     name: "Number"
//   },
//   {
//     sequence: 4,
//     text: "What type of property are you interested in?",
//     type: "options",
//     options: ["Apartment", "Villa", "Commercial", "Land", "Something else"],
//     name: "Intrested Property"
//   },
//   {
//     sequence: 5,
//     text: "What's your budget range?",
//     type: "text",
//     options: null,
//     name: "Budget"
//   },
//   {
//     sequence: 6,
//     text: "Any preferred locations?",
//     type: "text",
//     options: null,
//     name: "Location"
//   },
//   {
//     sequence: 7,
//     text: "How many bedrooms are you looking for?",
//     type: "options",
//     options: ["1 BHK", "2 BHK", "3 BHK", "4+ BHK"],
//     name: "BHK"
//   },
//   {
//     sequence: 8,
//     text: "Buying or renting?",
//     type: "options",
//     options: ["Buying", "Renting"],
//     name: "DealType"
//   },
//   {
//     sequence: 9,
//     text: "Any must-have features?",
//     type: "text",
//     options: null,
//     name:null
//   }
// ]);

