function hello() {
    console.log("Hello Docker World")
}


function echo({ message = "Hello Docker", loud=false}) {
    console.log(`Creating message, loud: ${loud}`)

    return `${message}${loud ? '!!!!!!!!!' : ''}`
}

export { hello, echo }