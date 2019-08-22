
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
            minEdgeSize: 0.1,
            maxEdgeSize: 2,
            minNodeSize: 1,
            maxNodeSize: 4,
            minArrowSize: 10
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
/*
            graph.nodes.push({
                id:  point[0],
                label: point[1],
                x: Math.random(),
                y: Math.random(),
                size: 3,
                color: '#000000'
            });
*/


            //cria o node
            node = {
                id: point[0],
                label: point[1],
                x: Math.random(),
                y: Math.random(),
                size: 3,
                color: '#000000'
            }

            s.graph.addNode(node)
            //console.log(node)

        }

    });


    // Ao receber os dados de um edge
    socket.on('get_edges', data =>
    {
        let counter = 0;

        for (let point of data)
        {
            //console.log(Object.keys(data).length);
/*
            graph.edges.push({
                id:  counter,
                source: point[0],
                target: point[1],
                color: '#000000',
                type: 'arrow'
            });
*/

            // cria um edge
            edge = {
                id: counter,
                source: point[0],
                target: point[1],
                color: "#404040",
                size:1,
                type:'arrow',
            }

            //graph.edges.push(edge);
            s.graph.addEdge(edge)

            counter++
        }

        ////////////////////////////////////////////////////////////////////

        // Carrega o grafo no sigma
        s.graph.read(graph);

        // Faz o sigma criar o grafo
        s.refresh();

        // inicia o algoritmo de espacialização
        s.startForceAtlas2({worker: true, barnesHutOptimize: false});

        //console.log('force atlas started')
        console.log(s.isForceAtlas2Running());

        // para o algoritmo apos 10s
        window.setTimeout(function() {s.killForceAtlas2()}, 10000);

        //console.log('testing!!!!')

        //console.log(graph)
        //console.log(s)

        ///////////////////////////////////////////////////////////////////


    });


});
