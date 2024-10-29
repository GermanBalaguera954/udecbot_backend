/* Contenedor principal del chat */
.chat - container {
    width: 100 %;
    max - width: 600px;
    height: 90vh;
    display: flex;
    flex - direction: column;
    justify - content: space - between;
    margin: 40px auto;
    padding: 20px;
    padding - left: 15px;
    padding - right: 15px;
    background - color: #00482B;
    border - radius: 20px;
    box - shadow: 0px 8px 20px rgba(0, 0, 0, 0.2);
    box - sizing: border - box;
}

@media(max - width: 768px) {
    .chat - container {
        height: 90vh;
        padding: 15px;
        padding - left: 15px;
        padding - right: 15px;
    }
}

@media(max - width: 480px) {
    .chat - container {
        height: 90vh;
        padding: 10px;
        padding - left: 15px;
        padding - right: 15px;
    }
}

@media(max - width: 320px) {
    .chat - container {
        height: 60vh;
        padding: 8px;
        padding - left: 10px;
        padding - right: 10px;
    }
}

  /* Contenedor del título UdecBot */
  .title - container {
    text - align: center;
    margin - bottom: 20px;
}

  /* Título del chatbot */
  .title {
    font - size: 24px;
    font - weight: bold;
    color: #FEBE12;
}

@media(max - width: 768px) {
    .title {
        font - size: 20px;
    }
}

@media(max - width: 480px) {
    .title {
        font - size: 18px;
    }
}

  /* Área de mensajes del chat */
  .messages - area {
    display: flex;
    flex - direction: column;
    position: relative;
    flex - grow: 1;
    overflow - y: auto;
    margin - bottom: 20px;
    padding: 15px;
    background - color: rgba(249, 249, 249, 0.8);
    background - image: url('../assets/images/escudo.png');
    background - size: contain;
    background - position: center;
    background - repeat: no - repeat;
    border - radius: 8px;
    box - shadow: inset 0px 1px 5px rgba(0, 0, 0, 0.1);
    scrollbar - width: thin;
    filter: brightness(0.8);
}

@media(max - width: 768px) {
    .messages - area {
        padding: 12px;
    }
}

@media(max - width: 480px) {
    .messages - area {
        padding: 8px;
    }
}

  /* Estilos para mensajes del usuario y del sistema */
  .message {
    margin - bottom: 10px;
    padding: 10px;
    max - width: 75 %;
    word - wrap: break-word;
    white - space: pre - wrap;
    box - shadow: 0px 1px 2px rgba(0, 0, 0, 0.15);
}
  
  .message.user {
    background - color: rgba(121, 192, 0, 0.3);
    color: #000;
    align - self: flex - end;
    border - radius: 15px 15px 0 15px;
}
  
  .message.bot {
    background - color: rgba(0, 72, 43, 0.9);
    color: #fff;
    align - self: flex - start;
    border - radius: 15px 15px 15px 0;
}

@media(max - width: 480px) {
    .message {
        max - width: 90 %;
        font - size: 14px;
        padding: 8px;
    }
}

  /* Contenedor del input de texto y el botón */
  .input - container {
    display: flex;
    align - items: center;
    padding: 10px;
    border - top: 2px solid #e0e0e0;
    background - color: #fafafa;
    border - radius: 12px;
}

@media(max - width: 768px) {
    .input - container {
        padding - top: 8px;
    }
}

@media(max - width: 480px) {
    .input - container {
        padding - top: 5px;
    }
}

  /* Campo de entrada de texto */
  .chat - input {
    flex - grow: 1;
    margin - right: 10px;
}
  
  .chat - input.MuiInputBase - root {
    padding: 1px;
    border - radius: 12px;
}

@media(max - width: 768px) {
    .chat - input.MuiInputBase - root {
        padding: 10px;
    }
}

@media(max - width: 480px) {
    .chat - input.MuiInputBase - root {
        padding: 8px;
        font - size: 14px;
    }
}

  /* Botón de enviar mensaje */
  .send - button {
    background - color: #007B3E;
    color: white;
    padding: 10px 20px;
    font - weight: bold;
    border - radius: 50px;
    border: none;
    cursor: pointer;
}
  
  .send - button:hover {
    background - color: #218838;
}

@media(max - width: 768px) {
    .send - button {
        padding: 8px 16px;
    }
}

@media(max - width: 480px) {
    .send - button {
        padding: 5px 12px;
        font - size: 12px;
    }
}
