// quando o conteudo da dom estiver carregado
document.addEventListener('DOMContentLoaded', () => {

    // Liga o websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);


    // Cria o grafo
    var graph = {
        nodes: [],
        edges: []
    };

    // Inicia o sigma
    var s = new sigma(
    {
        graph: graph,
        renderer: {
            container: document.getElementById('sigma-container'),
            type: 'canvas'
        },
        settings: {
            minEdgeSize: 2,
            maxEdgeSize: 2,
            minNodeSize: 1,
            maxNodeSize: 10,
            minArrowSize: 4
        }
    });


    // Pede pelos dados
    socket.emit('get_nodes');
    socket.emit('get_edges');


    // Ao receber os dados de um node
    socket.on('get_nodes', data =>
    {

        for (let point of data)
        {

            //cria o node
            node = {
                id: point[0],
                label: point[1],
                x: Math.random(),
                y: Math.random(),
                size: point[3],
                color: point[2]
            }

            // adiciona ao grafo
            s.graph.addNode(node)

        }

    });

    // Ao receber os dados de um edge
    socket.on('get_edges', data =>
    {
        let counter = 0;

        for (let point of data)
        {

            // cria um edge
            edge = {
                id: counter,
                source: point[0],
                target: point[1],
                color: "#707070",
                size:1,
                type:'arrow',
            }

            // adiciona ao grafo
            s.graph.addEdge(edge)

            counter++
        }

        // ajustes finais do grafo

        // Carrega o grafo no sigma
        s.graph.read(graph);

        // Faz o sigma criar o grafo
        s.refresh();

        ////////////////////////////////////////////////////////////////////////


/*
        // object with every neighbors of a node inside:
          sigma.classes.graph.addMethod('neighbors', function(nodeId) {
            var k,
                neighbors = {},
                index = this.allNeighborsIndex[nodeId] || {};

            for (k in index)
              neighbors[k] = this.nodesIndex[k];

            return neighbors;
          });

          sigma.parsers.json(
            graph,
          //sigma.parsers.json(
            //graph,
            //{
             // container: 'sigma-container'
            //},
            function(s) {
              // We first need to save the original colors of our
              // nodes and edges, like this:
              s.graph.nodes().forEach(function(n) {
                n.originalColor = n.color;
              });
              s.graph.edges().forEach(function(e) {
                e.originalColor = e.color;
              });

              // When a node is clicked, we check for each node
              // if it is a neighbor of the clicked one. If not,
              // we set its color as grey, and else, it takes its
              // original color.
              // We do the same for the edges, and we only keep
              // edges that have both extremities colored.
              s.bind('clickNode', function(e) {
                var nodeId = e.data.node.id,
                    toKeep = s.graph.neighbors(nodeId);
                toKeep[nodeId] = e.data.node;

                s.graph.nodes().forEach(function(n) {
                  if (toKeep[n.id])
                    n.color = n.originalColor;
                  else
                    n.color = '#eee';
                });

                s.graph.edges().forEach(function(e) {
                  if (toKeep[e.source] && toKeep[e.target])
                    e.color = e.originalColor;
                  else
                    e.color = '#eee';
                });

                // Since the data has been modified, we need to
                // call the refresh method to make the colors
                // update effective.
                s.refresh();
              });

              // When the stage is clicked, we just color each
              // node and edge with its original color.
              s.bind('clickStage', function(e) {
                s.graph.nodes().forEach(function(n) {
                  n.color = n.originalColor;
                });

                s.graph.edges().forEach(function(e) {
                  e.color = e.originalColor;
                });

                // Same as in the previous event:
                s.refresh();
              });
            }
          );




*/

        ////////////////////////////////////////////////////////////////////////

        // noverlap
        // Configura o noverlap layout
        var noverlapListener = s.configNoverlap({
            nodeMargin: 0.1,
            scaleNodes: 1.05,
            gridSize: 990,
            easing: 'quadraticInOut', // transicao da animacao
            duration: 3000   // duracao da animacao
        });


        // Bind
        noverlapListener.bind('start stop interpolate', function(e) {
            console.log(e.type);
            if(e.type === 'start') {
                console.time('noverlap');
            }
            if(e.type === 'interpolate') {
                console.timeEnd('noverlap');
            }
        });

        // inicia o algoritmo de espacialização
        s.startForceAtlas2({worker: true, barnesHutOptimize: false});

        // para o algoritmo apos 10s
        window.setTimeout(function() {s.killForceAtlas2(), s.startNoverlap()}, 10000 );




    });
});
