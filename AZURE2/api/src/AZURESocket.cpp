#include "AZURESocket.h"

#include "Constants.h"

bool AZURESocket::start() {
  // Create socket
  serverSocket_ = socket(AF_INET, SOCK_STREAM, 0);
  if (serverSocket_ == -1) {
    std::cerr << "Error creating socket." << std::endl;
      return false;
  }

  // Prepare the server address structure
  serverAddress_.sin_family = AF_INET;
  serverAddress_.sin_addr.s_addr = INADDR_ANY;
  serverAddress_.sin_port = htons(port_);

  int iSetOption = 1;
  setsockopt(serverSocket_, SOL_SOCKET, SO_REUSEADDR, (char*)&iSetOption, sizeof(iSetOption));

  // Bind the socket to a specific address and port
  if (bind(serverSocket_, (struct sockaddr *)&serverAddress_, sizeof(serverAddress_)) == -1) {
    std::cerr << "Error binding socket." << std::endl;
    return false;
  }

  // Listen for incoming connections
  if (listen(serverSocket_, 1) == -1) {
    std::cerr << "Error listening on socket." << std::endl;
    return false;
  }

  //std::cout << "Server started. Listening on port " << port_ << std::endl;

  socklen_t clientAddressSize = sizeof(clientAddress_);

  double buffer[BUFFER_SIZE*sizeof( uint64_t )];

  // Receive and process commands from the client
  while (true) {
    
    memset(buffer, 0, BUFFER_SIZE);

    // Accept incoming connections
    clientSocket_ = accept(serverSocket_, (struct sockaddr *)&clientAddress_, &clientAddressSize);
    if (clientSocket_ == -1) {
      std::cerr << "Error accepting connection." << std::endl;
      return false;
    }

    //std::cout << "Client connected." << std::endl;

    // Receive command from client
    ssize_t bytesRead = recv(clientSocket_, buffer, BUFFER_SIZE * sizeof( double ), 0);
    if (bytesRead == -1) {
      //std::cerr << "Error receiving data." << std::endl;
      //break;
    } 
    else if (bytesRead == 0) {
      //std::cout << "Client disconnected." << std::endl;
      //break;
    }

    // Process received command
    //std::cout << "Received command: " << buffer[0] << std::endl;
    //std::cout << "Received size: "    << buffer[1] << std::endl;

    // Initialize
    if( buffer[0] == 0 ){   
      api_->Initialize( );
      std::vector<bool> response;
      response.push_back( 1 );   
      sendPacket( response );
    }

    // Calculate segments from params
    if( buffer[0] == 1 ){   
      vector_r params;
      for( int i = 0; i < buffer[1]; ++i ){
        params.push_back( buffer[2+i] );
      }
      double nSegments = (double)api_->UpdateSegments( params );
      std::vector<double> response;
      response.push_back( nSegments );  
      sendPacket( response );
    }

    // Send the parameters
    if( buffer[0] == 2 ){
      api_->UpdateParameters( );
      vector_r response = api_->params_values( );
      sendPacket( response );
    }

    // Send the parameter name
    if( buffer[0] == 3 ){
      int idx = (int)buffer[1];
      api_->UpdateParameters( );
      std::string response = api_->params_names( idx );
      sendPacket( response );
    }

    // Send the parameter fixed
    if( buffer[0] == 4 ){
      api_->UpdateParameters( );
      std::vector<bool> response = api_->params_fixed( );
      sendPacket( response );
    }

    // Calculate external capture
    if( buffer[0] == 5 ){
      api_->CalculateExternalCapture( );
      std::vector<bool> response;
      response.push_back( 1 );
      sendPacket( response );
    }

    // Get data energies
    if( buffer[0] == 6 ){
      int idx = (int)buffer[2];
      vector_r response = api_->data_energies( idx );
      sendPacket( response );
    }

    // Get data segments
    if( buffer[0] == 7 ){
      int idx = (int)buffer[2];
      vector_r response = api_->data_segments( idx );
      sendPacket( response );
    }

    // Get data segments errors
    if( buffer[0] == 8 ){
      int idx = (int)buffer[2];
      vector_r response = api_->data_segments_errors( idx );
      sendPacket( response );
    }

    // Update data
    if( buffer[0] == 9 ){
      double nSegments = (double)api_->UpdateData( );
      std::vector<double> response;
      response.push_back( nSegments );
      sendPacket( response );
    }

    // Set to data mode
    if( buffer[0] == 10 ){
      api_->SetData( );
      std::vector<bool> response;
      response.push_back( 1 );
      sendPacket( response );
    }

    // Set to extrapolation mode
    if( buffer[0] == 11 ){
      api_->SetExtrap( );
      std::vector<bool> response;
      response.push_back( 1 );
      sendPacket( response );
    }

    // Get calculated segments
    if( buffer[0] == 12 ){
      int idx = (int)buffer[2];
      vector_r response = api_->calculated_segments( idx );
      sendPacket( response );
    }

    // Get calculated energies
    if( buffer[0] == 13 ){
      int idx = (int)buffer[2];
      vector_r response = api_->calculated_energies( idx );
      sendPacket( response );
    }

    // Change radius
    if( buffer[0] == 14 ){
      int idx = (int)buffer[2];
      double radius = (double)buffer[3];
      api_->SetRadius( idx, radius );
      std::vector<bool> response;
      response.push_back( 1 );
      sendPacket( response );
    }

    // Send the norms
    if( buffer[0] == 15 ){
      api_->UpdateNorms( );
      vector_r response = api_->norms( );
      sendPacket( response );
    }

    // Send the norms errors
    if( buffer[0] == 16 ){
      api_->UpdateNorms( );
      vector_r response = api_->norms_errors( );
      sendPacket( response );
    }

    close(clientSocket_);

  }

  // Close sockets
  close(clientSocket_);
  close(serverSocket_);

  return true;
}

bool AZURESocket::sendPacket( vector_r response ){

  double buffer[BUFFER_SIZE];
  memset(buffer, 0, BUFFER_SIZE);

  buffer[0] = response.size();
  for( int i = 0; i < response.size( ); ++i ) buffer[i+1] = response.at( i );

  // Send response back to the client
  int bytesSent = send(clientSocket_, &buffer, BUFFER_SIZE * sizeof( double ), 0);
  if (bytesSent == -1) {
    std::cerr << "Error sending data." << std::endl;
    //break;
  }

  return true;

}

bool AZURESocket::sendPacket( std::string response ){

  char buffer[BUFFER_SIZE];
  memset(buffer, 0, BUFFER_SIZE);

  buffer[0] = response.size();
  for( int i = 0; i < response.size( ); ++i ) buffer[i+1] = response.at( i );

  // Send response back to the client
  int bytesSent = send(clientSocket_, &buffer, BUFFER_SIZE * sizeof( std::string ), 0);
  if (bytesSent == -1) {
    std::cerr << "Error sending data." << std::endl;
    //break;
  }

  return true;

}

bool AZURESocket::sendPacket( std::vector<bool> response ){

  double buffer[BUFFER_SIZE];
  memset(buffer, 0, BUFFER_SIZE);

  buffer[0] = response.size();
  for( int i = 0; i < response.size( ); ++i ) buffer[i+1] = response.at( i );

  // Send response back to the client
  int bytesSent = send(clientSocket_, &buffer, BUFFER_SIZE * sizeof( double ), 0);
  if (bytesSent == -1) {
    std::cerr << "Error sending data." << std::endl;
    //break;
  }

  return true;

}